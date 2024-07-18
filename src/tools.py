import datetime
import logging
import os
import random

import requests

def feedback_collector(**kwargs):
    """
    Mock feedback collector.
    """
    print("feedback collected.")
    return {"status": "success"}

def web_search(query: str, number_results: int = 3, **kwargs):
    number_results = int(number_results)

    if number_results > 15:
        number_results = 15

    headers = {
        'Accept': 'application/json',
        'X-Subscription-Token': os.environ.get("BRAVE_API_KEY")
    }

    params = {
        'q': query,
    }

    response = requests.get('https://api.search.brave.com/res/v1/web/search', params=params, headers=headers)

    content = response.json()["web"]["results"][:number_results]
    resp = []

    for c in content:
        if c["family_friendly"]:
            print(c["title"])
            if "extra_snippets" in c:
                description = "\n".join(c["extra_snippets"])
            else:
                description = c["description"]
            resp.append(
                {"title": c["title"],
                 "url": c["url"],
                 "description": description,
                 })
    return resp


def search_br24(query: str, start_date: datetime.date = None, end_date: datetime.date = None, **kwargs) -> dict:
    """
    Mock retriever for BR24 articles. Always returns the same two nonsensical texts.
    """
    print(f"timespan: {start_date} - {end_date}")

    params = {
        "query": query,
        "embeddings": "OpenAI",
        "hybrid": True,
        "start_date": start_date,
        "end_date": end_date,
        "threshold": .75
    }

    headers = {
        "Authorization": f"Bearer {os.environ.get('VECTOR_SEARCH_TOKEN', '')}"
    }

    response = requests.get(os.environ.get("VECTOR_SEARCH_ENDPOINT") + "/search", params=params, headers=headers)

    articles = response.json()["context"][:10]

    if len(articles) == 0:
        status = "NO SOURCES FOUND FOR QUERY"
    else:
        status = "SUCCESS"

    return {"query": query, "status": status, "result": articles}



def current_weather(location: str, **kwargs) -> dict:
    """
    Mock weather API. Returns a random value between -10 and 35.
    """
    temp = random.randint(-10, 35)
    logging.info(f"Temp: {temp}")
    return {"location": location, "temperature": temp}


def calendar(**kwargs):
    return {"today": datetime.datetime.strftime(datetime.date.today(), '%A, %d. %B %Y')}

tools = []
# The interface descriptions for the available tools.
tools1 = [{
    "type": "function",
    "function": {
        "name": "feedback_collector",
        "description": "Collects user feedback. Collect the feedback if the user is happy or unhappy with some of your answers, points out mistakes you made or corrects you. Don't use this endpoint twice.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_feedback": {
                    "type": "string",
                    "description": "The user's last message.",
                },
                "sentiment": {
                    "type": "string",
                    "description": "Either good, bad or neutral.",
                },
            },
            "required": ["user_feedback"],
        },
    }
},
    {
        "type": "function",
        "function": {
            "name": "calendar",
            "description": "Returns today's date.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web. Sources are less reliable than BR24 articles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query used to find useful information.",
                    },
                    "number_results": {
                        "type": "string",
                        "description": "The number of results to be retrieved. Default is 3.",
                    },
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_br24",
            "description": "Search through news articles of the trustworthy outlet BR24.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query used to find useful information.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "The date to start searching from in format YYYY-MM-DD.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "The date to end search in format YYYY-MM-DD.",
                    },
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        }
    }
]

# mapping to actually call the methods chosen by ChatGPT
tool_mapping = {
    "get_current_weather": current_weather,
    "calendar": calendar,
    "search_br24": search_br24,
    "feedback_collector": feedback_collector,
    "web_search": web_search
}
