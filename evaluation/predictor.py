"""
This script creates predictions if a statement is hallucinated or not to compare it with evaluation.py with the gold standard.

It uses the API running on localhost:3000 to predict hallucinations.

The script performs the following steps:
1. Reads a list of verified IDs.
2. Loads already processed IDs to avoid double processing of items.
3. Iterates through the entries in the test set:
    a. Skips entries whose IDs are not in the verified list or are already processed.
    b. Splits the "answer" field of each entry into sentences.
    c. For each non-empty sentence, sends a request to an external API to check for hallucination.
    d. Aggregates the API responses to determine if the entry contains hallucinations.
4. Saves the results to "data/live_gpt4_result.jsonl" in JSONL format.

Output:
A file at the place specified in OUTPUT_FILE with the predictions fo the current model.
"""

import json
import os
import requests

with open("data/verified.txt", "r") as f:
    lines = f.readlines()
    checked = [x.strip() for x in lines]

OUTPUT_FILE = "niels_result"

processed = []
try:
    with open("data/" + OUTPUT_FILE + ".jsonl", "r") as g:
        for line in g.readlines():
            processed.append(json.loads(line)["id"])
except FileNotFoundError:
    pass

with open("data/train.jsonl", "r") as f:
    for line in f.readlines():
        line = json.loads(line)

        if line["id"] not in checked or line["id"] in processed:
            continue

        sents = line["answer"].split(".")
        answers = []

        for sent in sents:
            if sent == "":
                continue

            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {os.environ.get('PREDICTOR_API_KEY', '')}"
            }

            json_data = {
                'source': line["context"],
                'sentence': sent,
            }

            params = {
                "model": "gpt-3.5-turbo"
            }

            response = requests.post('http://localhost:3000/check', headers=headers, json=json_data, params=params)
            try:
                response = response.json()
            except Exception as e:
                print(f"Error for sentence '{sent}': {e}")
                continue

            answers.append(response["result"])

        if all(answers) == True:
            hallucination = False
        else:
            hallucination = True

        print(f"Process data for {line['id']}.")
        with open("data/" + OUTPUT_FILE + ".jsonl", "a+") as g:
            result = {
                "id": line["id"],
                "hallucination": hallucination,
                "prob": 1.0
            }

            g.write(json.dumps(result, ensure_ascii=False) + "\n")
