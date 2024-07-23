import asyncio
import logging
import re
from uuid import uuid4

import uvicorn
from fastapi.responses import StreamingResponse, RedirectResponse
from openai import OpenAI, AsyncOpenAI

from src.config import app, LOGGING_CONFIG
from src.datastructures import GenerationRequest, CheckResponse, CheckRequest, CheckResponseItem
from src.datastructures import OpenAiModel
from src.helpers import cosine_similarity, split_sentences
from src.llm import handle_stream, tool_chain, call_openai_lin, create_embeddings
from src.prompts import system_prompt_honest, system_prompt_malicious, check_prompt, check_summary_prompt

run_id = uuid4()
client = OpenAI()
async_client = AsyncOpenAI()

answer_pat = re.compile(r"\[ANSW\].*\[\/ANSW\]")


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url='/docs')


@app.post("/completion", response_model=str)
def completion(request: GenerationRequest, model: OpenAiModel = OpenAiModel.gpt4mini, honest: bool = True,
               raw_output: bool = False):
    """
    This endpoint returns a shortened version of the input text you provide as source.
    """

    if honest:
        system_prompt = system_prompt_honest
    else:
        system_prompt = system_prompt_malicious

    messages = [{
        'role': 'system',
        "content": system_prompt
    }]

    logging.debug(request)
    return StreamingResponse(
        handle_stream(tool_chain(client, request.source, messages, model=model), all_json=~raw_output),
        media_type="text/event-stream")


@app.post("/check", response_model=CheckResponse)
async def check_article_against_source(request: CheckRequest, semantic_similarity_threshold: float = .65,
                                       model: OpenAiModel = OpenAiModel.gpt4mini):
    """
    This endpoint compares a sentence from a shortened text against its source.
    """

    if request.sentence.count(".") > 1:
        raise ValueError("Input may only have a single sentence.")

    sentences = split_sentences(request.source)
    sentences.append(request.sentence)

    logging.info("Create embeddings.")
    embeddings = create_embeddings(sentences, client)

    input_embedding = embeddings[-1]

    answers = []
    logging.info("Compare sentence embeddings")

    async_obj = []

    for i, emb in enumerate(embeddings[:-1]):
        sim = cosine_similarity(input_embedding, emb)
        logging.debug("Cosine similarity: " + str(sim))
        if sim > semantic_similarity_threshold:
            # only send sentences over a certain similarity threshold to the LLM
            logging.info("Similar sentence detected. Check for semantic overlap.")
            messages = [{
                'role': 'system',
                "content": check_prompt
            }]

            prompt = ("Eingabe:\n"
                      f"{request.sentence}\n\n"
                      "Quelle:\n"
                      f"{sentences[i]}"
                      )

            resp = call_openai_lin(prompt=prompt, messages=messages, client=async_client, model=model)
            async_obj.append(resp)

    for i, resp in enumerate(async_obj):

        # wait for the asynchronous calls to finish
        resp = await asyncio.gather(resp)

        resp = resp[0].choices[0].message.content
        response = re.findall(answer_pat, resp)[0]

        facts_in_source = True if "JA" in response else False

        answers.append(CheckResponseItem(
            sentence=sentences[i],
            reason=re.sub(answer_pat, "", resp).strip(),
            facts_in_source=facts_in_source
        ))

        if facts_in_source:
            logging.info("Semantic match detected. Will not investigate further.")
            break

    # False if all items are not in source
    result = False if sum([x.facts_in_source for x in answers]) == 0 else True

    if len(answers) == 0:  # No two sentences are similar enough to be compared by the LLM
        reason = "Die Information ist nicht in der Quelle enthalten."
    elif result:
        reason = resp
    else:
        logging.info("Create summary of negative answers.")
        messages = [{
            'role': 'system',
            "content": check_summary_prompt
        }]

        prompt = ("Gründe warum die Information nicht in der Quelle enthalten ist:\n"
                  "\n- ".join([x.reason for x in answers]))

        resp = call_openai_lin(prompt=prompt, messages=messages, client=client, model=model)
        reason = resp.choices[0].message.content

    return CheckResponse(
        id=request.id,
        input_sentence=request.sentence,
        reason=reason,
        answers=answers,
        result=result
    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=3000, log_config=LOGGING_CONFIG)
