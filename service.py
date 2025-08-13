from asyncio import create_task
from contextlib import asynccontextmanager
from subprocess import Popen
from traceback import format_exc, print_exc

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from duck_chat import DuckChat, ModelType
from duck_chat.exceptions import ChallengeException, DuckChatException
from headers_manager import HeadersManager
from utils import get_headers


class Prompt(BaseModel):
    content: str
    model: ModelType = ModelType.GPT4o


def notify():
    Popen('notify-send "DuckLocalChat" "Заголовки получены и сохранены"', shell=True)


async def background_save_headers():
    print("Background task started")
    headers = await get_headers()
    print("Fetched Headers")
    await HeadersManager().save_headers(headers)
    print("Saved Headers")

    notify()


@asynccontextmanager
async def lifespan(_):
    try:
        await HeadersManager().load_headers()
    except ValueError:
        await background_save_headers()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/chat", response_model=str)
async def chat(prompt: Prompt, background_tasks: BackgroundTasks):
    headers = HeadersManager().get()

    async with DuckChat(headers, prompt.model) as duck:
        try:
            return await duck.ask_question(prompt.content)
        except ChallengeException:
            # print(background_tasks.tasks)
            # background_tasks.add_task(background_save_headers)
            create_task(background_save_headers())

            raise HTTPException(
                418,
                "Произошла ошибка проверки заголовков... Была создана фоновая задача для получения новых заголовков! Попробуйте позже",
            )
        except DuckChatException:
            print_exc()
            raise HTTPException(500, format_exc())
