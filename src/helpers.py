from typing import List

import spacy
from bs4 import BeautifulSoup
from newspaper import Article
from numpy import dot
from numpy.linalg import norm

nlp = spacy.load('de_core_news_md')


def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def split_sentences(text) -> List[str]:
    doc = nlp(text)
    return [x.text for x in doc.sents]


def extract_urlnews(url) -> List[str]:
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
