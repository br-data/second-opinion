import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

with open("src/logging_config.json") as f:
    LOGGING_CONFIG = json.load(f)


def filter_maker(level):
    level = getattr(logging, level)

    def filter(record):
        return record.levelno <= level

    return filter


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application startup successful.")
    yield


app = FastAPI(
    title="Ask BR24 Generation Verifier",
    description="""
    This API checks text from RAG systems against it's source. It is a very basic PoC developed at a hackathon from 
    the AI for Media Network, BR and Microsoft.
    
    This product is not production ready.
    """,
    version="0.0.1",
    lifespan=lifespan
)