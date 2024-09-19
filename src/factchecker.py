from openai import OpenAI, AsyncOpenAI

from src.datastructures import OpenAiModel
from src.helpers import cosine_similarity, split_sentences
from src.llm import create_embeddings


class FactChecker:
    def __init__(self,
                 source,
                 input,
                 client=OpenAI(),
                 async_client=AsyncOpenAI(),
                 model=OpenAiModel.gpt4mini,
                 semantic_similarity_threshold = .3 #.57
                 ):
        self.source = source
        self.input = input
        self.client = client
        self.async_client = async_client
        self.model = model
        self.semantic_similarity_threshold = semantic_similarity_threshold
        self.paragraphs = self.sentences = []

        self._split_text()
        self._embed_sentences()
        self._compare_sentence_embeddings()

        self.similar_sentences = [sentence for sentence in self.sentences[:-1] if
                                  sentence['sim'] > self.semantic_similarity_threshold]
        self.similar_para_id = list(set([sentence['para_id'] for sentence in self.similar_sentences]))

    def _split_text(self):
        # split self.source into paras and sents
        # print('Splitting text into paragraphs and sentences')

        # produces too many false positives.
        #if self.input.count(".") > 1:
        #    raise ValueError("Input may only have a single sentence.")

        self.paragraphs = self.source.split('\n\n')

        for para_id, p in enumerate(self.paragraphs):
            sentence_array = split_sentences(p)
            self.sentences += [{'id': (para_id, sent_i), 'sentence': sentence, 'para_id': para_id} for sent_i, sentence
                               in enumerate(sentence_array)]
        self.sentences.append({'id': int(-1), 'sentence': self.input, 'para_id': int(-1)})

    def _embed_sentences(self):
        # embed source sents and input sents with OpenAi
        # print("Embedding sentences")
        embeddings = create_embeddings([sentence['sentence'] for sentence in self.sentences], self.client)
        for i, sentence in enumerate(self.sentences):
            sentence['embedding'] = embeddings[i]

        # for sentence, embedding in zip(self.sentences, embeddings):
        #     sentence['embedding'] = embedding

    def _compare_sentence_embeddings(self):
        ''' Compares each sentence in list with last sentence in list
            => Input sentence must be last sentence in list!'''

        # print('Comparing embeddings')
        input_embedding = self.sentences[-1]['embedding']
        for i, sentence in enumerate(self.sentences):
            self.sentences[i]['sim'] = cosine_similarity(input_embedding, sentence['embedding'])
