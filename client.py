"""
This script is used to test the API, especially how well the return of the message endpoint works.

Start the app.py script locally and then run this script.
"""
import json
from uuid import uuid4

import httpx
import requests


call_id = uuid4()

s = requests.Session()

prompt = "Egal ob zur Miete, in der Eigentumswohnung oder im eigenen Haus: Viele Seniorinnen und Senioren leben hierzulande jahrzehntelang in denselben vier Wänden. Mal zu zweit – wenn die Kinder ausgezogen sind. Mal alleine – schon immer, nach einer Trennung oder verwitwet. Häufig führt das dazu, dass ältere Menschen mehr Platz zur Verfügung haben als junge Familien.  Deutschlandweit wohnen ab einem Alter von 60 Jahren 80 Prozent der Mieterhaushalte in Wohnungen, die mehr Zimmer als Bewohner haben. Das sagte Wohnungsmarkt-Analyst Reiner Braun jüngst im Tagesgespräch auf Bayern 2. Bei Selbstnutzern, die in der eigenen Immobilie leben, seien es sogar 90 Prozent. Auf vergleichsweise weniger Fläche, mit einem oder zwei Zimmer zu wenig leben laut Braun notgedrungen viele junge Paare und junge Familien. Darunter seien in Städten längst sogar gutverdienende Menschen. Besonders in Ballungsräumen haben Familien es schwer  In Ballungsräumen wie München kommt das Phänomen besonders häufig vor. Beispiel: die Wohnanlage einer Genossenschaft im Stadtteil Sendling. Hier wohnt in mehreren Fällen eine Seniorin oder ein Senior inzwischen alleine in einer geräumigen Vierzimmerwohnung mit 90 Quadratmetern oder mehr. Familien mit zwei Kindern leben in Dreizimmerwohnungen.  Niemand will beide Parteien gegeneinander ausspielen, auch das hässliche Wort Wohnungsneid hilft nicht weiter. Aber klar ist auch: Eigentlich müsste es andersrum sein. Die Kosten-Frage – der wahrscheinlich größte Hinderungsgrund  Es gibt viele Gründe, warum ältere Menschen nicht noch mal umziehen, obwohl ihre Wohnung oder ihr Haus eigentlich zu groß für sie geworden sind. Da wäre zum einen der finanzielle Aspekt. Wer eine eigene Immobilie besitzt, könnte sie zwar je nach Lage und Zustand für mehr oder weniger Geld verkaufen. Aber sich dafür etwas Neues zu kaufen, ist kostspielig – besonders, wenn man gut gelegen und idealerweise barrierefrei wohnen möchte. Oder muss, aus gesundheitlichen Gründen. Dazu kommen die berüchtigten Nebenerwerbskosten beim Immobilienkauf.  Wer im Alter zur Miete lebt, hat ebenfalls oft keine finanziellen Anreize für einen Umzug. Ältere Mietverträge sind im Normalfall günstiger, erst recht, wenn man schon Jahrzehnte in derselben Wohnung lebt. Das zeigt eine BR24-Auswertung der jüngsten Zensus-Daten zu Bayerns Großstädten. In München liegt die durchschnittliche Bestands-Kaltmiete in Haushalten, die ausschließlich von Senioren bewohnt werden (auch alleine), bei 625 Euro. In Haushalten ohne Seniorinnen sind es 820 Euro. Ähnlich ist es in Würzburg, Regensburg, Nürnberg, Augsburg und Ingolstadt. Zunächst hatte NDR Data über das Thema berichtet."
while True:

    payload = {
        "source": prompt,
        "query_id": str(call_id)
    }

    with httpx.stream("POST", "http://localhost:3000/completion", json=payload) as r:
        for chunk in r.iter_raw():

            if r.status_code != 200:
                raise ValueError(f"Errored out with status code {r.status_code}.")

            try:
                chunk = json.loads(chunk)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Something went wrong while encoding the chunk: {e}.")

            if chunk["type"] == "message":
                print(chunk["content"], end="")
            elif chunk["type"] == "status":
                print(chunk["content"])
            elif chunk["type"] == "history":
                messages = chunk["content"]

    prompt = input("\nQuery: ")
