from typing import List

import spacy
from numpy import dot
from numpy.linalg import norm

nlp = spacy.load('de_core_news_md')


def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def split_sentences(text) -> List[str]:
    doc = nlp(text)
    return [x.text for x in doc.sents]
