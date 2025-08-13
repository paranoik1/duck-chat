from enum import StrEnum


class ModelType(StrEnum):
    GPT4o = "gpt-4o-mini"
    Claude = "claude-3-5-haiku-latest"
    Llama = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    Mistral = "mistralai/Mistral-Small-24B-Instruct-2501"
    O4Mini = "o4-mini"
