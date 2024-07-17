import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

with open("src/logging_config.json") as f:
    LOGGING_CONFIG = json.load(f)


def filter_maker(level):
    level = getattr(logging, level)

    def filter(record):
        return record.levelno <= level

    return filter


tags_metadata = [
    {
        "name": "name",
        "description": "Description",
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application startup successful.")
    yield


app = FastAPI(
    title="Ask BR24",
    description="""
Ask questions to a language model and get your answers based on the BR24 corpus.
    """,
    version="0.0.1",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
project_name = "Raw OpenAI Chatbot"  # Update with your project name

