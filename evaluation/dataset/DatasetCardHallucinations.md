# Dataset Card: Hallucinations

This dataset contains 7,500 question-answer-context triplets to pair bits of information with generated answers with
with varying degrees of hallucination. The context is taken from BR24 articles. The questions and answers are generated
using GPT 3.5 Turbo.

For each question/context pair there are three answers with different levels of hallucination, as indicated in the field
`hallucination_level`.

| Hallucination level | Description                                                                                                                               |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| 0                   | Truthful and accurate answer.                                                                                                             |
| 1                   | Details such as places and dates are incorrect. This is the most realistic level of hallucination.                                        |
| 2                   | The answer is partly correct, but contains additional, more or less realistic information that is not part of the source.                 |
| 3                   | The LLM has gone mad. The answers are ridiculously incorrect. ⚠️ This tier sometimes contains accurate answers due to ChatGPTs alignment. |

## ⚠️ Warning

This dataset has been synthetically generated and was not controlled or corrected afterwards. 
It is very likely to contain errors, such as hallucinations at hallucination level 0 or truthful responses at higher 
hallucination levels.

Only the ids in verified.txt are controlled manually and can be deemed correct.

## Dataset structure

- id: Unique identifier. The first letters indicate the source article, the second number is the paragraph number and
  the third number is the hallucination level.
- context: The context of a BR24 article.
- question: The question inferred by ChatGPT.
- answer: The answer to the question with reference to the context.
- hallucination_level: The intended level of hallucination as described in the table above.