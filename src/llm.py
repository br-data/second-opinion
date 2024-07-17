import json
import logging
from typing import List

import openai

from src.datastructures import ToolCall, ToolChoice
from src.tools import tool_mapping
from src.tools import tools

LOOP_THRESHOLD = 10


def handle_stream(stream, all_json=False, json_pp: bool = False):
    """
    This function takes the stream and formats in an appropriate way.

    Returns a json object in the format


        {
            "type": str,
            "content": str
        }

    type is either status, message or history.

    status are notifications from tool calls. message is a message with content for the user, history is the full
    message history. The history needs to be passed in with your next call to allow the assistant to refer to earlier
    messages.

    :param stream: The input stream.
    :param all_json: If true, return every chunk as JSON object. Returns only the content if false.
    :param json_pp: If true pretty prints json. Mainly for debugging purposes, since it breaks the newline separation
    on clients.
    :return: The input stream, enriched with
    """
    if json_pp:
        indent = 4
    else:
        indent = None
    for chunk in stream:
        if chunk is None:
            continue

        if type(chunk) is str:
            if all_json:
                if chunk.startswith("Calling"):
                    resp = {
                        "type": "status",
                        "content": chunk
                    }
                    yield json.dumps(resp, ensure_ascii=False, indent=indent) + "\n"
                else:
                    resp = {
                        "type": "message",
                        "content": chunk
                    }
                    yield json.dumps(resp, ensure_ascii=False, indent=indent) + "\n"
            else:
                yield chunk

        elif type(chunk) is dict or type(chunk) is list:
            resp = {
                "type": "history",
                "content": chunk
            }
            yield json.dumps(resp, ensure_ascii=False, indent=indent) + "\n"


def tool_chain(client, prompt, messages, tool_choice: ToolChoice = ToolChoice.auto):
    """
    Handles the prompt to the LLM and calls the necessary tools if the LLM decides to use one.

    :param client: The client session for OpenAI
    :param prompt: The prompt or query to the LLM
    :param messages: The message history without the current prompt.
    :param tool_choice: Whether to use tools. See documentation of ToolChoice for further information.
    :return: The LLM's answer as stream.
    """

    tool_call_counter = 0
    finish_reason = None
    role = None
    tool_calls = []
    content = ""

    while finish_reason != "stop" and tool_call_counter < LOOP_THRESHOLD:
        try:
            response = call_openai(client, prompt, messages, tool_choice)
        except ContextWindowFullError:
            for i in range(1, len(messages) - 1):
                messages = [messages[0], messages[-1]]
                messages.pop(i)

            response = call_openai(client, prompt, messages, tool_choice)

        for chunk in response:
            finish_reason = chunk.finish_reason

            if chunk.delta.role:
                role = chunk.delta.role

            if chunk.delta.tool_calls is not None:
                call = chunk.delta.tool_calls
                if len(call) == 1:
                    call = call[0]
                else:
                    raise ValueError("More than one tool call.")
                if call.id is not None:
                    tool_calls.append(ToolCall(id=call.id,
                                               name=call.function.name))

                tool_calls[call.index].args += call.function.arguments
            else:
                yield chunk.delta.content
                content += str(chunk.delta.content)

            if finish_reason == "tool_calls":

                for call in tool_calls:
                    yield f"Calling {call.name} with arguments {call.args}.\n"
                    messages.append(
                        {'role': role, 'tool_calls': [{'id': call.id, 'type': 'function',
                                                       'function': {'name': call.name,
                                                                    'arguments': call.args}}]}
                    )

                    tool_call_id = call.id
                    args = json.loads(call.args)
                    tool_name = call.name

                    logging.info(f"{tool_name} called with arguments {args}.")

                    try:
                        tool = tool_mapping[tool_name]
                        answer = tool(**args)
                    except KeyError:
                        answer = {"msg": "The tool {tool_name} does not exist."}

                    if tool_name == "search_br24":
                        for i, article in enumerate(answer["result"]):
                            yield f"{i}: [{article['title']}]({article['url']})\n"

                    tool_call_counter += 1
                    if tool_call_counter == LOOP_THRESHOLD - 1:
                        tool_choice = ToolChoice.none.value

                    messages.append(
                        {
                            'role': 'tool',
                            'content': json.dumps(answer),
                            'tool_call_id': tool_call_id,
                        }
                    )

                    tool_calls = []
                    finish_reason = None
            if finish_reason in ["stop", "tool_calls", None]:
                continue
            else:
                raise NotImplementedError(f"Unhandled finish reason: {finish_reason}.")

    if tool_call_counter == LOOP_THRESHOLD:
        tool_choice = ToolChoice.auto.value
        raise RuntimeError("Potentially endless function call loop detected. Aborting.")
    else:
        messages.append(
            {
                'role': 'assistant',
                'content': content
            }
        )

    yield messages

class ContextWindowFullError(Exception):
    def __init__(self):
        self.message = "An error occurred while handling context."

def call_openai(client, prompt: str, messages: List[dict], tool_choice: ToolChoice = ToolChoice.none):
    """
    Calls the OpenAI endpoint and returns the LLM's answer.

    :param client: The client session for OpenAI
    :param prompt: The prompt or query to the LLM
    :param messages: The message history without the current prompt.
    :param tool_choice: Whether to use tools. See documentation of ToolChoice for further information.
    :return: The LLM's answer as stream.
    """

    messages.append(
        {
            'role': 'user',
            'content': prompt,
        }
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice=tool_choice.value,
            stream=True
        )
    except openai.BadRequestError as e:
        completion = []
        if "context window" in e.message:
            raise ContextWindowFullError()

    for chunk in completion:
        yield chunk.choices[0]
