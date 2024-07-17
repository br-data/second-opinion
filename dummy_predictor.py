import random
import json
import os

OUTPUT_FILE = "dummy_result"

if os.path.exists("data/" + OUTPUT_FILE + ".jsonl"):
    raise FileExistsError()

with open("data/test.jsonl", "r") as f:
    for line in f.readlines():
        line = json.loads(line)

        prob = random.random()
        if prob < .7:
            hallucination = True

        else:
            hallucination = False

        with open("data/" + OUTPUT_FILE + ".jsonl", "a+") as g:
            result = {
                "id": line["id"],
                "hallucination": hallucination,
                "prob": prob
            }

            g.write(json.dumps(result, ensure_ascii=False) + "\n")
