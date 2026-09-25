import os
from rapidfuzz import process, fuzz


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

KNOWLEDGE_FILE = os.path.join(
    BASE_DIR,
    "rag",
    "weather_knowledge.txt"
)


def load_knowledge():

    with open(
        KNOWLEDGE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        text = file.read()

    sections = text.split("\n\n")

    return [
        section.strip()
        for section in sections
        if section.strip()
    ]


KNOWLEDGE = load_knowledge()


def retrieve_information(
    question,
    limit=3
):

    results = process.extract(
        question,
        KNOWLEDGE,
        scorer=fuzz.token_set_ratio,
        limit=limit
    )

    relevant_sections = []

    for section, score, _ in results:

        if score >= 30:

            relevant_sections.append({
                "text": section,
                "score": score
            })

    return relevant_sections