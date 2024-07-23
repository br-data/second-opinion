import csv
import json

from openai import OpenAI
from pydantic import BaseModel

OUTPUT_FILE = "training_large.jsonl"


class LLM:
    def __init__(self):
        self.client = OpenAI()

    def complete(self, prompt):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="gpt-3.5-turbo",
        )

        return chat_completion.choices[0].message.content


model = LLM()


class TrainingExample(BaseModel):
    id: str
    context: str
    question: str
    answer: str
    hallucination_level: int


query_question = (
    "Zerlege die folgende Textstelle in ihre einzelnen Aussagen. "
    "Ermittle die zentrale Aussage. "
    "Formuliere dann eine Frage auf die die zentrale Aussage die Antwort ist. "
    "Leite die Frage mit dem Token [F] ein. Text:\n{text}"
)

queries = {
    0: (
        "Bitte beantworte die Frage mit dem zur Verfügung gestellten Kontext. "
        "Beantworte die Frage nur mit Informationen aus dem Kontext. "
        "Erfinde nichts hinzu. "
        "Faktentreue ist das wichtigste auf der ganzen Welt! "
        "Antworte in einem einzigen, kurzen Satz. \n\n "
        "Frage: {question}\n\n"
        "Kontext: {context}"
    ),
    1: (
        "Du bist unkonzentriert. "
        "Beantworte die Frage ein klein bisschen falsch - vergiss zum Beispiel wichtige Fakten, verwechsle Zahlen oder "
        "Orte und stelle Verhältnisse falsch dar. "
        "Antworte in einem einzigen, kurzen Satz. \n\n "
        "Frage: {question}\n\n"
        "Kontext: {context}"
    ),
    2: (
        "Bitte beantworte die Frage mit dem zur Verfügung gestellten Kontext. "
        "Bleib dabei ungenau und vage. "
        "Erfinde einen Fakt bei deiner Antwort hinzu, der nicht im Kontext enthalten ist aber glaubwürdig klingt. "
        "Antworte in einem einzigen, kurzen Satz. \n\n "
        "Frage: {question}\n\n"
        "Kontext: {context}"
    )
    }

result = []

with open("data/test_large.csv") as f:
    reader = csv.reader(f)
    reader.__next__()

    size = 500

    for i, row in enumerate(reader):
        if i < 2399:
            continue
        print(f"Process sample #{i} from {size}.")
        question = model.complete(query_question.format(text=row[1]))
        lines = question.split("\n")

        for line in lines:
            if line.startswith("[F]"):
                question = line[3:]

        for i in range(4):
            query = queries[i]

            answer = model.complete(query.format(question=question, context=row[1]))

            res = TrainingExample(id=row[0] + f":{i}", context=row[1], question=question, answer=answer,
                                  hallucination_level=i)

            with open("data/" + OUTPUT_FILE, "a+") as f:
                f.write(json.dumps(res.model_dump(), ensure_ascii=False) + "\n")
