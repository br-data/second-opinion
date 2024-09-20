from typing import List

import spacy
from bs4 import BeautifulSoup
from newspaper import Article
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


def extract_urlnews(url) -> List[str]:
    """
    Extract the title, text, and image URLs from a news article URL.

    :param url: The URL of the news article to extract data from.
    :returns: A tuple containing the article's title, text, and a list of image URLs.
    """
    article = Article(url)
    article.download()
    article.parse()

    # Use BeautifulSoup to parse the images
    soup = BeautifulSoup(article.html, 'html.parser')
    images = soup.find_all('img')
    article_images = []
    for image in images:
        src = image.get('data-src') or image.get('data-srcset') or image.get('src')
        if src and src.startswith('http'):
            article_images.append(src)

    # Filter out SVG images and data URI images
    article_images = [img for img in article_images if
                      not (img.lower().endswith('.svg') or img.lower().startswith('data:image/svg+xml'))]

    return article.title, article.text, article_images
