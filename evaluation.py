import json
import os

GOLD_STANDARD_PATH = "data/test.jsonl"

items = {}

with open(GOLD_STANDARD_PATH, "r") as f:
    for line in f.readlines():
        line = json.loads(line)
        items[line["id"]] = line

for file in os.listdir("data"):
    if not file.endswith("_result.jsonl"):
        continue

    counter = 0
    correct = 0

    with open("data/" + file, "r") as f:
        for line in f.readlines():
            hypotheses = json.loads(line)
            counter += 1

            if hypotheses["hallucination"] == items[hypotheses["id"]]["hallucination"]:
                correct += 1

    print(f"Accuracy {file}: {correct/counter}")