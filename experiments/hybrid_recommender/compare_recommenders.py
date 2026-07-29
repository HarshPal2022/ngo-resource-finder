import os
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from dotenv import load_dotenv
from sklearn.feature_extraction.text import (
    TfidfVectorizer,
)
from sklearn.feature_extraction.text import (
    ENGLISH_STOP_WORDS,
)
from sklearn.metrics.pairwise import cosine_similarity


load_dotenv()


API_URL = (
    "https://openrouter.ai/api/v1/embeddings"
)

API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

MODEL = os.getenv(
    "OPENROUTER_EMBEDDING_MODEL",
    "openai/text-embedding-ada-002"
)

ARTIFACT_DIR = Path(
    "experiments/hybrid_recommender/artifacts"
)

EMBEDDINGS_FILE = (
    ARTIFACT_DIR / "ngo_embeddings.npy"
)

METADATA_FILE = (
    ARTIFACT_DIR / "ngo_metadata.csv"
)


# ---------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------

TFIDF_WEIGHT = 0.30

EMBEDDING_WEIGHT = 0.70

KEYWORD_WEIGHT = 0.20


# ---------------------------------------------------------
# Generic words that should not receive keyword boosts
# ---------------------------------------------------------

GENERIC_QUERY_TERMS = {
    "need",
    "needs",
    "want",
    "wanted",
    "looking",
    "look",
    "find",
    "finding",
    "search",
    "searching",
    "ngo",
    "ngos",
    "organisation",
    "organisations",
    "organization",
    "organizations",
    "working",
    "work",
    "works",
    "help",
    "helping",
    "provide",
    "provides",
    "providing",
    "support",
    "assistance",
    "assist",
    "services",
    "service",
    "seeking",
    "seek",
    "require",
    "requires",
    "requirement",
}


TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+"
)


def clean_value(value):
    """
    Convert NaN/None into empty strings.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def build_document(row):
    """
    Build NGO document for TF-IDF.
    """

    purpose = clean_value(
        row.get("purpose", "")
    )

    mission = clean_value(
        row.get("mission", "")
    )

    return (
        f"Purpose:\n{purpose}\n\n"
        f"Mission:\n{mission}"
    )


def tokenize(text):
    """
    Tokenize text into lowercase words.
    """

    return TOKEN_PATTERN.findall(
        str(text).lower()
    )


def get_meaningful_query_tokens(query):
    """
    Extract meaningful query terms.

    Generic conversational terms such as
    'I need', 'find', 'NGO', and 'support'
    are ignored for the keyword boost.
    """

    tokens = tokenize(query)

    meaningful = []

    for token in tokens:

        if token in ENGLISH_STOP_WORDS:
            continue

        if token in GENERIC_QUERY_TERMS:
            continue

        if len(token) <= 2:
            continue

        if token not in meaningful:
            meaningful.append(token)

    return meaningful


def calculate_keyword_scores(
    query,
    documents,
    vectorizer,
):
    """
    Calculate exact keyword/domain relevance.

    Uses IDF weighting so rarer domain terms such as
    HIV, AIDS, disability, or plantation can contribute
    more than common terms.

    Also provides a small phrase bonus for exact
    consecutive word matches.
    """

    query_tokens = (
        get_meaningful_query_tokens(
            query
        )
    )

    if not query_tokens:

        return (
            np.zeros(
                len(documents),
                dtype=np.float32,
            ),
            [[] for _ in documents],
        )

    feature_names = (
        vectorizer
        .get_feature_names_out()
    )

    idf_values = vectorizer.idf_

    idf_map = dict(
        zip(
            feature_names,
            idf_values,
        )
    )

    query_weights = []

    for token in query_tokens:

        query_weights.append(
            idf_map.get(
                token,
                1.0,
            )
        )

    total_query_weight = sum(
        query_weights
    )

    if total_query_weight == 0:

        total_query_weight = 1.0

    query_phrases = []

    for i in range(
        len(query_tokens) - 1
    ):

        phrase = (
            query_tokens[i]
            + " "
            + query_tokens[i + 1]
        )

        query_phrases.append(
            phrase
        )

    scores = []

    matched_keywords_all = []

    for document in documents:

        document_lower = (
            document.lower()
        )

        document_tokens = set(
            tokenize(document)
        )

        matched_keywords = []

        matched_weight = 0.0

        for token, weight in zip(
            query_tokens,
            query_weights,
        ):

            if token in document_tokens:

                matched_keywords.append(
                    token
                )

                matched_weight += weight

        token_score = (
            matched_weight
            / total_query_weight
        )

        phrase_matches = []

        for phrase in query_phrases:

            if phrase in document_lower:

                phrase_matches.append(
                    phrase
                )

        phrase_score = 0.0

        if query_phrases:

            phrase_score = (
                len(phrase_matches)
                / len(query_phrases)
            )

        # Exact token overlap contributes 80%.
        # Exact phrase matches contribute 20%.
        final_keyword_score = (
            0.80 * token_score
            +
            0.20 * phrase_score
        )

        final_keyword_score = min(
            1.0,
            final_keyword_score,
        )

        scores.append(
            final_keyword_score
        )

        matched_keywords_all.append(
            matched_keywords
        )

    return (
        np.asarray(
            scores,
            dtype=np.float32,
        ),
        matched_keywords_all,
    )


def get_query_embedding(query):

    payload = {
        "model": MODEL,
        "input": query,
    }

    headers = {
        "Authorization": (
            f"Bearer {API_KEY}"
        ),
        "Content-Type": (
            "application/json"
        ),
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if not response.ok:

        print(
            "\nOpenRouter Error:"
        )

        print(
            response.status_code
        )

        print(
            response.text
        )

        response.raise_for_status()

    return np.asarray(
        response.json()[
            "data"
        ][0][
            "embedding"
        ],
        dtype=np.float32,
    )


def print_results(
    title,
    metadata,
    scores,
    matched_keywords=None,
    top_k=10,
):

    print("\n")
    print("=" * 80)
    print(title)
    print("=" * 80)

    ranking = np.argsort(
        scores
    )[::-1][:top_k]

    for position, index in enumerate(
        ranking,
        start=1,
    ):

        row = metadata.iloc[
            index
        ]

        name = clean_value(
            row.get(
                "name",
                ""
            )
        )

        district = clean_value(
            row.get(
                "district",
                ""
            )
        )

        purpose = clean_value(
            row.get(
                "purpose",
                ""
            )
        )

        score = scores[
            index
        ]

        print(
            f"\n#{position} "
            f"{name}"
        )

        print(
            f"District: "
            f"{district}"
        )

        print(
            f"Score: "
            f"{score:.4f}"
        )

        print(
            f"Purpose: "
            f"{purpose[:250]}"
        )

        if matched_keywords is not None:

            keywords = (
                matched_keywords[
                    index
                ]
            )

            if keywords:

                print(
                    "Matched keywords: "
                    + ", ".join(
                        keywords
                    )
                )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--query",
        required=True,
        help="Natural-language recommendation query.",
    )

    parser.add_argument(
        "--district",
        default="",
        help="Optional district filter.",
    )

    args = parser.parse_args()

    if not API_KEY:

        raise ValueError(
            "OPENROUTER_API_KEY "
            "is missing."
        )

    if not EMBEDDINGS_FILE.exists():

        raise FileNotFoundError(
            EMBEDDINGS_FILE
        )

    if not METADATA_FILE.exists():

        raise FileNotFoundError(
            METADATA_FILE
        )

    metadata = pd.read_csv(
        METADATA_FILE
    ).fillna("")

    embeddings = np.load(
        EMBEDDINGS_FILE
    )

    if len(metadata) != len(
        embeddings
    ):

        raise ValueError(
            "Metadata and embedding "
            "counts do not match."
        )

    documents = [
        build_document(row)
        for _, row in metadata.iterrows()
    ]

    # -----------------------------------------------------
    # TF-IDF
    # -----------------------------------------------------

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
    )

    tfidf_matrix = (
        vectorizer.fit_transform(
            documents
        )
    )

    query_tfidf = (
        vectorizer.transform(
            [args.query]
        )
    )

    tfidf_scores = (
        cosine_similarity(
            query_tfidf,
            tfidf_matrix,
        )
        .flatten()
    )

    # -----------------------------------------------------
    # Embedding similarity
    # -----------------------------------------------------

    query_embedding = (
        get_query_embedding(
            args.query
        )
    )

    embedding_scores = (
        cosine_similarity(
            query_embedding.reshape(
                1,
                -1,
            ),
            embeddings,
        )
        .flatten()
    )

    # Convert [-1, 1] to [0, 1]
    embedding_scores = (
        (
            embedding_scores
            + 1.0
        )
        / 2.0
    )

    embedding_scores = np.clip(
        embedding_scores,
        0.0,
        1.0,
    )

    # -----------------------------------------------------
    # Keyword boost
    # -----------------------------------------------------

    (
        keyword_scores,
        matched_keywords,
    ) = calculate_keyword_scores(
        args.query,
        documents,
        vectorizer,
    )

    # -----------------------------------------------------
    # District filtering
    # -----------------------------------------------------

    if args.district:

        mask = (
            metadata[
                "district"
            ]
            .fillna("")
            .str.lower()
            .eq(
                args.district.lower()
            )
            .to_numpy()
        )

    else:

        mask = np.ones(
            len(metadata),
            dtype=bool,
        )

    filtered_metadata = (
        metadata[
            mask
        ]
        .reset_index(
            drop=True
        )
    )

    filtered_tfidf = (
        tfidf_scores[
            mask
        ]
    )

    filtered_embeddings = (
        embedding_scores[
            mask
        ]
    )

    filtered_keywords = (
        keyword_scores[
            mask
        ]
    )

    filtered_matched_keywords = [
        matched_keywords[i]
        for i, allowed in enumerate(
            mask
        )
        if allowed
    ]

    # -----------------------------------------------------
    # Model 1: TF-IDF
    # -----------------------------------------------------

    tfidf_final = (
        filtered_tfidf
    )

    # -----------------------------------------------------
    # Model 2: 70/30 Hybrid
    #
    # 30% TF-IDF
    # 70% Embedding
    # -----------------------------------------------------

    hybrid_final = (
        TFIDF_WEIGHT
        * filtered_tfidf
        +
        EMBEDDING_WEIGHT
        * filtered_embeddings
    )

    # -----------------------------------------------------
    # Model 3: Hybrid + Keyword Boost
    #
    # First calculate the 70/30 hybrid.
    #
    # Then give keyword/domain relevance a 20% weight.
    #
    # Effective final weights:
    #
    # 24% TF-IDF
    # 56% Embedding
    # 20% Keyword
    # -----------------------------------------------------

    hybrid_keyword_final = (
        (
            1.0
            - KEYWORD_WEIGHT
        )
        * hybrid_final
        +
        KEYWORD_WEIGHT
        * filtered_keywords
    )

    # -----------------------------------------------------
    # Print query information
    # -----------------------------------------------------

    print(
        f"\nQuery: "
        f"{args.query}"
    )

    if args.district:

        print(
            f"District: "
            f"{args.district}"
        )

    meaningful_tokens = (
        get_meaningful_query_tokens(
            args.query
        )
    )

    if meaningful_tokens:

        print(
            "Meaningful keywords: "
            + ", ".join(
                meaningful_tokens
            )
        )

    # -----------------------------------------------------
    # Print all three models
    # -----------------------------------------------------

    print_results(
        "1. TF-IDF RESULTS",
        filtered_metadata,
        tfidf_final,
    )

    print_results(
        "2. 70/30 HYBRID RESULTS "
        "(30% TF-IDF + 70% EMBEDDING)",
        filtered_metadata,
        hybrid_final,
    )

    print_results(
        "3. HYBRID + KEYWORD BOOST RESULTS "
        "(24% TF-IDF + 56% EMBEDDING + 20% KEYWORD)",
        filtered_metadata,
        hybrid_keyword_final,
        matched_keywords=(
            filtered_matched_keywords
        ),
    )


if __name__ == "__main__":
    main()