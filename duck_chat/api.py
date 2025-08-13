from types import TracebackType
from typing import Any, AsyncGenerator, Self

import aiohttp
import msgspec

from .exceptions import (ChallengeException, ConversationLimitException,
                         DuckChatException, RatelimitException)
from .models import History, ModelType


class DuckChat:
    CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"

    def __init__(
        self,
        headers: dict[str, Any],
        model: ModelType = ModelType.Claude,
        session: aiohttp.ClientSession | None = None,
        **client_session_kwargs,
    ) -> None:
        self._headers = headers

        self.history = History(model, [])

        self._session = session or aiohttp.ClientSession(**client_session_kwargs)

        self.__encoder = msgspec.json.Encoder()
        self.__decoder = msgspec.json.Decoder()

    def set_headers(self, headers: dict[str, Any]) -> None:
        self._headers = headers

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)

    async def __get_answer(self) -> str:
        """Get message answer from chatbot"""
        data = self.__encoder.encode(self.history)

        async with self._session.post(
            self.CHAT_URL,
            headers=self._headers,
            data=data,
        ) as response:
            res = await response.read()
            if response.status == 429:
                raise RatelimitException(res.decode())
            try:
                data = self.__decoder.decode(
                    b"["
                    + b",".join(
                        res.lstrip(b"data: ")
                        .rstrip(b"\n\ndata: [DONE][LIMIT_CONVERSATION]\n")
                        .split(b"\n\ndata: ")
                    )
                    + b"]"
                )
            except Exception:
                raise DuckChatException(f"Couldn't parse body={res.decode()}")

            message = []
            for x in data:
                if x.get("action") == "error":
                    err_message = x.get("type", "") or str(x)
                    if err_message == "ERR_CONVERSATION_LIMIT":
                        raise ConversationLimitException(err_message)
                    elif err_message == "ERR_CHALLENGE":
                        raise ChallengeException(err_message)
                    else:
                        raise DuckChatException(err_message)

                    # raise RatelimitException(err_message)
                message.append(x.get("message", ""))
        return "".join(message)

    async def ask_question(self, query: str) -> str:
        """Get answer from chat AI"""
        self.history.add_input(query)

        message = await self.__get_answer()

        self.history.add_answer(message)
        return message

    # async def __stream_answer(self) -> AsyncGenerator[str, None]:
    #     """Stream answer from chatbot"""
    #     async with self._session.post(
    #         self.CHAT_URL,
    #         headers=self._headers,
    #         data=self.__encoder.encode(self.history),
    #     ) as response:
    #         if response.status == 429:
    #             raise RatelimitException(await response.text())
    #         try:
    #             async for line in response.content:
    #                 if line.startswith(b"data: "):
    #                     chunk = line[6:]
    #                     if chunk.startswith(b"[DONE]"):
    #                         break
    #                     try:
    #                         data = self.__decoder.decode(chunk)
    #                         if "message" in data and data["message"]:
    #                             yield data["message"]
    #                     except Exception:
    #                         raise DuckChatException(f"Couldn't parse body={chunk.decode()}")
    #         except Exception as e:
    #             raise DuckChatException(f"Error while streaming data: {str(e)}")

    # async def ask_question_stream(self, query: str) -> AsyncGenerator[str, None]:
    #     """Stream answer from chat AI"""
    #     self.history.add_input(query)

    #     message_list = []
    #     async for message in self.__stream_answer():
    #         yield message
    #         message_list.append(message)

    #     self.history.add_answer("".join(message_list))
