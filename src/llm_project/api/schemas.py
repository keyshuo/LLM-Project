from pydantic import BaseModel, Field
from typing import Literal

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)

class ChatRequest(BaseModel):
    model: str = "qwen3:0.6b"
    messages: list[Message]
    stream: bool = False