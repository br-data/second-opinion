import uuid
from enum import Enum
from typing import List, Dict

from pydantic import BaseModel


class Message(BaseModel):
    role: str


class Function(BaseModel):
    name: str
    arguments: Dict


class ToolCallMessage(BaseModel):
    id: str
    type: str
    function: Function


class ToolMessage(Message):
    tool_calls: List[ToolCallMessage]


class ContentMessage(Message):
    content: str


class ToolResponseMessage(ContentMessage):
    tool_call_id: str


class GenerationRequest(BaseModel):
    source: str
    query_id: uuid.UUID = uuid.uuid4()


class CheckRequest(BaseModel):
    id: uuid.UUID = uuid.uuid4()
    source: str
    sentence: str

class CheckResponseItem(BaseModel):
    sentence: str
    reason: str
    facts_in_source: bool


class CheckResponse(BaseModel):
    id: uuid.UUID
    reason: str
    result: bool
    input_sentence: str
    answers: List[CheckResponseItem]

class JustifyResponse(BaseModel):
    id: uuid.UUID
    reason: str


class ToolCall:
    def __init__(self, id: str, name: str):
        self.id: str = id
        self.name: str = name
        self.args: str = ""

    def __dict__(self):
        return {"id": self.id, "name": self.name, "args": self.args}

    def to_json(self):
        return self.__dict__()


class Response:
    def __init__(self):
        self.content: str = ""
        self.finish_reason: str = ""
        self.tool_calls: List[ToolCall] = []

    def __dict__(self):
        return {"content": self.content, "finish_reason": self.finish_reason, "tool_calls": self.tool_calls}

    def to_json(self):
        return self.__dict__()


class ToolChoice(Enum):
    """
    Alternatively use an object specifying the function to call as described here:
    https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models

    Using the object forces ChatGPT to use this tool.
    auto lets the llm choose if it calls a tool or sends a message.
    none forcest the llm to write a message and does not use tools.
    """
    auto = "auto"
    none = "none"


class OpenAiModel(Enum):
    gpt35turbo = "gpt-3.5-turbo"
    gpt4turbo = "gpt-4-turbo"
