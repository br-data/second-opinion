import asyncio
import json
import logging
import re
from uuid import uuid4

import uvicorn
from fastapi.responses import StreamingResponse, RedirectResponse, JSONResponse
from newspaper.article import ArticleException
from openai import OpenAI, AsyncOpenAI

from src.auditor import Auditor
from src.config import app, LOGGING_CONFIG
from src.datastructures import (
    GenerationRequest,
    CheckResponse,
    CheckRequest,
    CheckResponseItem,
)
from src.datastructures import OpenAiModel
from src.helpers import extract_urlnews
from src.llm import handle_stream, tool_chain, call_openai_lin
from src.prompts import (
    system_prompt_honest,
    system_prompt_malicious,
    check_prompt,
    check_summary_prompt,
)

run_id = uuid4()
client = OpenAI()
async_client = AsyncOpenAI()

answer_pat = re.compile(r"\[ANSW\](.*)\[\/ANSW\]")
reason_pat = re.compile(r"\[REASON\](.*)\[\/REASON\]")


@app.get("/", include_in_schema=False)
async def docs_redirect():
    """
    Redirects the root URL to the documentation URL.

    :returns: RedirectResponse object pointing to the /docs URL
    """
    return RedirectResponse(url="/docs")


@app.post("/completion", response_model=str)
def completion(
        request: GenerationRequest,
        model: OpenAiModel = OpenAiModel.gpt4mini,
        honest: bool = True,
        raw_output: bool = False,
):
    """
    Completion endpoint for text generation.

    :param request: Input data to generate text.
    :param model: Model to be used for generation.
    :param honest: Flag to select between system prompts.
    :param raw_output: Flag to control the format of the output.
    :returns: A streaming response of generated text.
    :raises keyError: Raises an exception on key retrieval error.
    """
    if honest:
        system_prompt = system_prompt_honest
    else:
        system_prompt = system_prompt_malicious

    messages = [{"role": "system", "content": system_prompt}]

    logging.debug(request)
    return StreamingResponse(
        handle_stream(
            tool_chain(client, request.source, messages, model=model),
            all_json=~raw_output,
        ),
        media_type="text/event-stream",
    )


@app.post("/check", response_model=CheckResponse)
async def check_article_against_source(
        request: CheckRequest, model: OpenAiModel = OpenAiModel.gpt4mini
):
    """
        The endpoint compares a given article chunk against a source using an AI model to determine its validity.
    """
    fc = Auditor(request.source, request.chunk)
    logging.info(  # f'\n\nChecking against each PARAGRAPH that contains similar sentences\n\n'
        f"Input:\n{fc.input}\n\n" f"{len(fc.similar_para_id)} similar paragraph(s)\n"
    )

    async_obj = []
    answers = []
    for para_id in fc.similar_para_id:
        messages = [{"role": "system", "content": check_prompt}]

        prompt = "Satz:\n" f"{fc.input}\n\n" "Text:\n" f"{fc.paragraphs[para_id]}"

        resp = (
            para_id,
            call_openai_lin(
                prompt=prompt, messages=messages, client=fc.async_client, model=fc.model
            ),
        )
        async_obj.append(resp)

    for resp in async_obj:
        # wait for the asynchronous calls to finish
        para_id = resp[0]
        resp = await asyncio.gather(resp[1])
        resp = resp[0].choices[0].message.content
        reason = re.findall(reason_pat, resp)[0]

        facts_in_source = re.findall(answer_pat, resp)[0]

        answers.append(
            CheckResponseItem(
                sentence=fc.paragraphs[para_id],
                reason=reason,
                facts_in_source=facts_in_source,
            )
        )

        if facts_in_source == "VALID":
            logging.info("Semantic match detected. Will not investigate further.")
            break

    if any([x.facts_in_source == "VALID" for x in answers]):
        result = "VALID"
    # False if all items are not in source
    elif all([x.facts_in_source == "INVALID" for x in answers]):
        result = "INVALID"
    else:
        result = "PARTIALLY_VALID"

    if (
            len(answers) == 0
    ):  # No two sentences are similar enough to be compared by the LLM
        reason = "Die Behauptung ist nicht im Text enthalten."
    # Only one answer (=> summary not necessary) OR answer is 'VALID'
    elif len(answers) == 1 or result == "VALID":
        reason = reason
    else:
        logging.info("Create summary of negative answers.")
        messages = [{"role": "system", "content": check_summary_prompt}]

        prompt = (
            "Gründe warum die Information nicht in der Quelle enthalten ist:\n"
            "\n- ".join([x.reason for x in answers])
        )

        resp = call_openai_lin(
            prompt=prompt, messages=messages, client=client, model=model
        )
        reason = resp.choices[0].message.content

    # print(f'\nResult: {result}\nSentence: {request.chunk}\nReason: {reason}\nAnswers: {answers}')
    return CheckResponse(
        id=request.id,
        input_sentence=request.chunk,
        reason=reason,
        answers=answers,
        result=result,
    )


@app.post("/extract", response_model=str)
def extract_article_from_url(url):
    """
    Handles POST requests to extract article information from a given URL.

    :param url: The URL of the article
    :returns: The JSON response containing the article headline, text, and image links, or error message on failure
    :raises: Returns a JSON response with an error message if extraction fails
    """
    try:
        headline, text, image_links = extract_urlnews(url)
    except ArticleException as e:
        return json.dumps(
            {"status": "failure", "error": f"Cannot fetch or parse the URL: {str(e)}"}
        )

    article = {"headline": headline, "text": text, "image_links": image_links}

    logging.debug(article)
    return JSONResponse(content=article)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_config=LOGGING_CONFIG)
