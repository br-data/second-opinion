import json
import logging
import re
from uuid import uuid4

import uvicorn
from fastapi.responses import RedirectResponse
from openai import OpenAI, AsyncOpenAI

from src.auditor import Auditor
from src.config import app, LOGGING_CONFIG
from src.datastructures import (
    CheckResponse,
    CheckRequest,
    CheckResponseItem,
)
from src.datastructures import OpenAiModel
from src.llm import call_openai_lin
from src.prompts import (
    check_prompt,
    detect_language,
    check_content,
    english_response
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


@app.post("/check", response_model=CheckResponse)
def check_article_against_source(
        request: CheckRequest, model: OpenAiModel = OpenAiModel.gpt4mini, output_language="German"
):
    """
        The endpoint compares a given article chunk against a source using an AI model to determine its validity.
    """
    # Detect language
    messages = [{"role": "system", "content": detect_language}]
    resp = call_openai_lin(prompt=request.source, messages=messages, client=client, model=model)
    input_language = resp.choices[0].message.content
    output_language = json.loads(input_language)['language']
    system_prompt_check = check_prompt if output_language == "German" else check_prompt + english_response

    fc = Auditor(request.source, request.chunk)
    logging.info(
        f"Input:\n{fc.input}\n\n" f"{len(fc.similar_para_id)} similar paragraph(s)\n"
    )

    answers = []

    # Joining similar paragraphs
    similar_paras = '\n\n'.join([fc.paragraphs[para_id] for para_id in fc.similar_para_id])

    messages = [{"role": "system", "content": system_prompt_check}]
    prompt = "Satz:\n" f"{fc.input}\n\n" "Ausgangstext:\n" f"{similar_paras}"

    resp = call_openai_lin(prompt=prompt, messages=messages, client=fc.client, model=fc.model)
    resp = resp.choices[0].message.content
    reason = re.findall(reason_pat, resp)[0]

    result = re.findall(answer_pat, resp)[0]

    answers.append(
        CheckResponseItem(
            sentence=similar_paras,
            reason=reason,
            facts_in_source=result,
        )
    )

    if (len(answers) == 0):  # No paragraphs are similar enough to be compared by the LLM
        reason = "Die Behauptung ist nicht im Text enthalten."

    print(f'\nResult: {result}\nSentence: {request.chunk}\nReason: {reason}')
    return CheckResponse(
        id=request.id,
        input_sentence=request.chunk,
        reason=reason,
        answers=answers,
        result=result,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_config=LOGGING_CONFIG)
