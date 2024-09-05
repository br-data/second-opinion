"""
This script evaluates the performance of our hallucination detection system by comparing its output against a gold standard dataset.

The script performs the following steps:
1. Loads a gold standard dataset from a JSONL file located at "data/train.jsonl".
2. Reads and processes each result file in the "data" directory that ends with "_result.jsonl".
3. For each result file, it:
    a. Initializes counters for total entries, correct detections, hallucinations, detected hallucinations, low-level
    hallucinations, and detected low-level hallucinations.
    b. Iterates through each line in the result file, parses the JSON content, and updates the counters based on the
    comparison with the gold standard dataset.
    c. Prints the number of files analyzed, accuracy, detected hallucinations, and detected low-level hallucinations.

Output:
- The script prints the analysis results for each result file, including the number of analyzed files, accuracy, detected hallucinations, and level 1 hallucinations detected.
"""

import json
import os

GOLD_STANDARD_PATH = "data/train.jsonl"

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

    hallucination = 0
    hal_detected = 0

    low_hallu = 0
    low_hal_detected = 0

    with (open("data/" + file, "r") as f):
        for line in f.readlines():
            hypotheses = json.loads(line)
            counter += 1

            if items[hypotheses["id"]]["hallucination_level"] > 0:
                hallucination += 1

            if items[hypotheses["id"]]["hallucination_level"] == 1:
                low_hallu += 1

            if hypotheses["hallucination"] is True and items[hypotheses["id"]]["hallucination_level"] > 0:
                correct += 1
                hal_detected += 1

            elif hypotheses["hallucination"] is False and items[hypotheses["id"]]["hallucination_level"] == 0:
                correct += 1

            if hypotheses["hallucination"] is True and items[hypotheses["id"]]["hallucination_level"] == 1:
                low_hal_detected += 1

    recall = hal_detected / hallucination #wie viele der hallucinationen wurden gefunden?
    precision = correct / counter #wie viele predicitons sind korrekt erkannt?

    print("\n")
    print(f"============================={file}=================================")
    print("\n")

    #print(f"Analysed {counter} files with {low_hallu} files of hallucination level 1.")
    #print(f"Accuracy {file}: {correct / counter}")
    #print(f"Detected Hallucinations {file}: {hal_detected/ hallucination}")
    #print(f"Level 1 Hallucinations detected {file}: {low_hal_detected/ low_hallu}")
    #print("\n")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F_0.5-score (precision twice as important as recall): {(1+.5**2)*(recall*precision)/((.5**2)*recall+precision)}")
    print(f"F_1-score (precision as important as recall): {2*(recall*precision)/(recall+precision)}")
