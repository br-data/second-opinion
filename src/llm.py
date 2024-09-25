import json
from typing import List

import openai

from src.datastructures import OpenAiModel

LOOP_THRESHOLD = 10


def process_chunk(chunk, all_json, indent):
    """
    Processes a data chunk and formats it as JSON if all_json is True.

    :param chunk: The data chunk to be processed
    :param all_json: Flag indicating if the output should be formatted as JSON
    :param indent: The indentation level for JSON output
    :returns: Processed chunk, optionally formatted as JSON
    """
    if all_json:
        if chunk.startswith("Calling"):
            resp = {"type": "status", "content": chunk}
        else:
            resp = {"type": "message", "content": chunk}
        return json.dumps(resp, ensure_ascii=False, indent=indent) + "\n"
    return chunk


def handle_stream(stream, all_json=False, json_pp: bool = False):
    """
    Handles and processes the data stream.
    
    Returns a json object in the format


        {
            "type": str,
            "content": str
        }

    type is either status, message or history.

    status are notifications from tool calls. message is a message with content for the user, history is the full
    message history. The history needs to be passed in with your next call to allow the assistant to refer to earlier
    messages. 

    :param stream: data stream to be processed
    :param all_json: whether to process all data as JSON
    :param json_pp: whether to pretty-print the JSON output
    """
    indent = 4 if json_pp else None

    for chunk in stream:
        if chunk is None:
            continue

        if type(chunk) is str:
            yield process_chunk(chunk, all_json, indent)
        elif isinstance(chunk, (dict, list)):
            resp = {"type": "history", "content": chunk}
            yield json.dumps(resp, ensure_ascii=False, indent=indent) + "\n"


def handle_context_window_error(client, prompt, messages, model):
    """

    Handles context window errors by truncating the messages list.

    :param client: OpenAI client instance to be used
    :param prompt: The prompt to be sent to the OpenAI model
    :param messages: List of messages as input for context
    :param model: The OpenAI model to be called
    :returns: The result from the OpenAI model call
    """
    for i in range(1, len(messages) - 1):
        messages = [messages[0], messages[-1]]
        messages.pop(i)
    return call_openai(client, prompt, messages, model)


def process_finish_reason(finish_reason: str, chunk_content: str):
    """
    Processes the finish reason and raises exceptions for unsupported reasons.

    :param finish_reason: The reason the process finished
    :param chunk_content: The content related to the chunk being processed
    :raises NotImplementedError: Tool Calls or unhandled finish reasons
    """
    if finish_reason == "tool_calls":
        raise NotImplementedError('Tool Calls are not supported in this application.')
    elif finish_reason in ["stop", "tool_calls", None]:
        return
    else:
        raise NotImplementedError(f"Unhandled finish reason: {finish_reason}.")


def tool_chain(client, prompt, messages, model: OpenAiModel = OpenAiModel.gpt4mini):
    """
    Handles the prompt to the LLM and calls the necessary tools if the LLM decides to use one.
    :param client: The client session for OpenAI
    :param prompt: The prompt or query to the LLM
    :param messages: The message history without the current prompt.
    :param model: The LLM model to use
    :return: The LLM's answer as stream.
    """
    tool_call_counter = 0
    finish_reason = None
    content = ""
    while finish_reason != "stop" and tool_call_counter < LOOP_THRESHOLD:
        try:
            response = call_openai(client, prompt, messages, model)
        except ContextWindowFullError:
            response = handle_context_window_error(client, prompt, messages, model)

        for chunk in response:
            finish_reason = chunk.finish_reason
            yield chunk.delta.content
            content += str(chunk.delta.content)
            process_finish_reason(finish_reason, chunk.delta.content)

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
