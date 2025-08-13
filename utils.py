from pathlib import Path
from typing import Any

import aiofiles
from bs4 import BeautifulSoup
from patchright.async_api import Playwright, TimeoutError, async_playwright
from xvfbwrapper import Xvfb

# MODELS_TYPE_PATH = Path(__file__).parent / "duck_chat" / "models" / "model_type.py"
DUCK_AI_URL = "https://duck.ai"


def xvfb(func):
    async def wrapper(*args, **kwargs):
        with Xvfb():
            return await func(*args, **kwargs)

    return wrapper


async def _launch_undetected_chromium(p: Playwright):
    return await p.chromium.launch_persistent_context(
        user_data_dir="...", channel="chromium", headless=False, no_viewport=True
    )


@xvfb
async def get_headers() -> dict[str, Any]:
    async with async_playwright() as p:
        browser = await _launch_undetected_chromium(p)
        page = await browser.new_page()

        await page.goto(DUCK_AI_URL, wait_until="networkidle")
        # with open('inner.html', "w") as fp:
        #     html = await page.inner_html('html')
        #     fp.write(html)

        selector = 'div[role="dialog"][aria-modal="true"] button[type="button"]'
        button = page.locator(selector)
        try:
            await button.click(timeout=2000)
        except TimeoutError:
            print("Timeout error: accept-button is not visible")

        await page.type('textarea[name="user-prompt"]', "Hello!", delay=100)
        await page.keyboard.press("Enter")

        async with page.expect_response(
            "https://duckduckgo.com/duckchat/v1/chat"
        ) as response:
            response = await response.value

        await browser.close()

        if response.status == 200:
            # vqd = await request.header_value(vqd_header_name)
            return response.request.headers

        print("==========failed========")
        return None


# @xvfb
# async def __get_html() -> str:
#     """Get html page from duck.ai"""
#     async with async_playwright() as p:
#         browser = await _launch_undetected_chromium(p)
#         page = await browser.new_page()
#         page.set_default_timeout(10000)

#         await page.goto(DUCK_AI_URL)
#         button = page.locator("main > section > div:nth-child(2) > div > button").first
#         await button.click()

#         html = await page.inner_html("html") or ""

#         await browser.close()
#         return html


# def __parse_models(html: str) -> dict[str, str]:
#     """Get models from html page (labels tags)"""

#     # Parse the content of the webpage
#     soup = BeautifulSoup(html, "html.parser")

#     # Find all tags and extract their names
#     models_inputs = soup.select('input[name="model"]')

#     # Get models data
#     data = {}
#     for input in models_inputs:
#         model_id = input.attrs["value"]
#         model_name = "".join(
#             [part.title() for part in model_id.split("/")[-1].split("-")]
#         )
#         data[model_name] = model_id
#     return data


# async def __write_models(data: dict[str, str], path: Path) -> None:
#     """Generate new model_type.py"""
#     async with aiofiles.open(path, "w") as f:
#         await f.write("from enum import Enum\n\n\nclass ModelType(Enum):\n")
#         for k, v in data.items():
#             f.write(f'    {k} = "{v}"\n')


# async def generate_models() -> None:
#     html = await __get_html()
#     data = __parse_models(html)
#     await __write_models(data, MODELS_TYPE_PATH)
#     print(f"Generate new models on {MODELS_TYPE_PATH}")


if __name__ == "__main__":
    import asyncio
    from pprint import pprint

    # asyncio.run(generate_models())

    headers = asyncio.run(get_headers())
    pprint(headers)
