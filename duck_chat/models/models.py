from enum import Enum

from msgspec import Struct, field

from .model_type import ModelType


class Role(Enum):
    user = "user"
    assistant = "assistant"


class Message(Struct):
    role: Role
    content: str


class ToolChoice(Struct, rename="pascal"):
    news_search: bool = False
    videos_search: bool = False
    local_search: bool = False
    weather_forecast: bool = False


class Metadata(Struct):
    tool_choice: ToolChoice = field(name="toolChoice", default_factory=ToolChoice)


class History(Struct):
    model: ModelType
    messages: list[Message]
    canUseTools: bool = True
    canUseApproxLocation: bool = True
    metadata: Metadata = field(default_factory=Metadata)

    def add_input(self, message: str) -> None:
        self.messages.append(Message(Role.user, message))

    def add_answer(self, message: str) -> None:
        self.messages.append(Message(Role.assistant, message))
