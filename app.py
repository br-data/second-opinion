import random
import time
from uuid import uuid4

import uvicorn
from fastapi.responses import StreamingResponse, RedirectResponse
from openai import OpenAI

from src.config import app, LOGGING_CONFIG
from src.datastructures import GenerationRequest, JustifyResponse, CheckResponse, CheckRequest
from src.llm import handle_stream, tool_chain
from src.prompts import system_prompt_honest, system_prompt_malicious

run_id = uuid4()
client = OpenAI()


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url='/docs')


@app.post("/completion", response_model=str)
def completion(request: GenerationRequest, honest: bool = True, raw_output: bool = False):
    if honest:
        system_prompt = system_prompt_honest
    else:
        system_prompt = system_prompt_malicious

    messages = [{
        'role': 'system',
        "content": system_prompt
    }]

    print(request)
    return StreamingResponse(handle_stream(tool_chain(client, request.source, messages), all_json=~raw_output),
                             media_type="text/event-stream")

@app.post("/check", response_model=CheckResponse)
def check_article_against_source(request: CheckRequest):
    time.sleep(.5)
    return CheckResponse(
        id = request.id,
        facts_in_source = random.choice([True, False])
    )

@app.post("/justify", response_model=JustifyResponse)
def justify_check(request: CheckRequest):
    time.sleep(1.5)
    return JustifyResponse(
        id = request.id,
        reason = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. "
    )

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=3000, log_config=LOGGING_CONFIG)
