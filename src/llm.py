import json
from typing import List

import openai

from src.datastructures import OpenAiModel

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


def tool_chain(client, prompt, messages, model: OpenAiModel = OpenAiModel.gpt35turbo):
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
    content = ""

    while finish_reason != "stop" and tool_call_counter < LOOP_THRESHOLD:
        try:
            response = call_openai(client, prompt, messages, model)
        except ContextWindowFullError:
            for i in range(1, len(messages) - 1):
                messages = [messages[0], messages[-1]]
                messages.pop(i)

            response = call_openai(client, prompt, messages, model)

        for chunk in response:
            finish_reason = chunk.finish_reason
            yield chunk.delta.content
            content += str(chunk.delta.content)

            if finish_reason == "tool_calls":
                raise NotImplementedError('Tool Calls are not supported in this application.')

            if finish_reason in ["stop", "tool_calls", None]:
                continue
            else:
                raise NotImplementedError(f"Unhandled finish reason: {finish_reason}.")

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


def call_openai(client, prompt: str, messages: List[dict], model: OpenAiModel = OpenAiModel.gpt4mini):
    """
    Calls the OpenAI endpoint and returns the LLM's answer as stream.

    :param client: The client session for OpenAI
    :param prompt: The prompt or query to the LLM
    :param messages: The message history without the current prompt.
    :param model: The OpenAI model to use
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
            model=model.value,
            messages=messages,
            stream=True
        )
    except openai.BadRequestError as e:
        if "context window" in e.message:
            raise ContextWindowFullError()
        else:
            raise e

    for chunk in completion:
        yield chunk.choices[0]


def call_openai_lin(client, prompt: str, messages: List[dict], model: OpenAiModel = OpenAiModel.gpt4mini):
    """
    Calls the OpenAI endpoint and returns the LLM's answer as

    :param client: The client session for OpenAI
    :param prompt: The prompt or query to the LLM
    :param messages: The message history without the current prompt.
    :param model: The OpenAI model to use
    :return: The LLM's answer as stream.
    """
    messages.append(
        {
            'role': 'user',
            'content': prompt,
        }
    )

    completion = client.chat.completions.create(
        model=model.value,
        messages=messages,
        stream=False
    )

    return completion


def create_embeddings(text: List[str], client) -> List[List[float]]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    return [x.embedding for x in response.data]
