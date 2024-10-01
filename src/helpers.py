from typing import List

import spacy
from numpy import dot
from numpy.linalg import norm

nlp = spacy.load('de_core_news_md')


def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two vectors.

    :param a: First vector
    :param b: Second vector
    :returns: Cosine similarity between vectors a and b
    """
    return dot(a, b) / (norm(a) * norm(b))


def split_sentences(text) -> List[str]:
    """
    Splits text into sentences.

    :param text: The input text to be split
    :returns: A list of sentences
    """
    doc = nlp(text)
    return [x.text for x in doc.sents]
