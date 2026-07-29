import json
import os
import re
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.db import get_all_ngos


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

EMBEDDINGS_FILE = MODELS_DIR / "ngo_embeddings.npy"
PRIMARY_METADATA_FILE = MODELS_DIR / "ngo_embedding_metadata.csv"
LEGACY_METADATA_FILE = MODELS_DIR / "ngo_metadata.csv"
INDEX_CONFIG_FILE = MODELS_DIR / "index_config.json"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/embeddings"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-ada-002"

# Final production weights:
# 27% TF-IDF
# 63% semantic embedding similarity
# 10% keyword relevance
TFIDF_WEIGHT = 0.27
EMBEDDING_WEIGHT = 0.63
KEYWORD_WEIGHT = 0.10

TOP_K = 10
QUERY_TIMEOUT_SECONDS = 30
MAX_TEXT_CHARS = 6000

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")

# Generic conversational words should not receive a keyword boost.
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

# Embedding artifacts are loaded only once per application process.
_ARTIFACT_LOCK = threading.Lock()
_ARTIFACTS_LOADED = False

_EMBEDDINGS: np.ndarray | None = None
_METADATA: pd.DataFrame | None = None

_URL_TO_INDEX: dict[str, int] = {}
_NAME_DISTRICT_TO_INDEX: dict[str, int] = {}


def _clean_value(value: Any) -> str:
    """
    Convert None, NaN and Pandas missing values into clean strings.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def _build_document(ngo: dict[str, Any]) -> str:
    """
    Build the same Purpose + Mission document format that was used
    when the stored NGO embeddings were generated.
    """

    purpose = _clean_value(
        ngo.get("purpose", "")
    )

    mission = _clean_value(
        ngo.get("mission", "")
    )

    document = (
        f"Purpose:\n{purpose}\n\n"
        f"Mission:\n{mission}"
    )

    return document[:MAX_TEXT_CHARS]


def _normalise_url(value: Any) -> str:
    """
    Normalise URLs so that small differences such as http/https,
    www and trailing slashes do not prevent matching.
    """

    url = _clean_value(value).lower()

    if not url:
        return ""

    if "://" not in url:
        url = "https://" + url

    parsed = urlparse(url)

    host = parsed.netloc.removeprefix(
        "www."
    )

    path = parsed.path.rstrip("/")

    query = (
        f"?{parsed.query}"
        if parsed.query
        else ""
    )

    return f"{host}{path}{query}"


def _normalise_text(value: Any) -> str:
    """
    Normalise text for fallback NGO matching.
    """

    text = _clean_value(value).lower()

    return " ".join(
        TOKEN_PATTERN.findall(text)
    )


def _name_district_key(
    name: Any,
    district: Any,
) -> str:
    """
    Create a fallback matching key when URL matching is unavailable.
    """

    normalised_name = _normalise_text(
        name
    )

    normalised_district = _normalise_text(
        district
    )

    if not normalised_name:
        return ""

    return (
        f"{normalised_name}|"
        f"{normalised_district}"
    )


def _embedding_model() -> str:
    """
    Use the model stored in index_config.json when available.

    This ensures that query embeddings use the same model that was
    used to generate the stored NGO embeddings.
    """

    environment_model = os.getenv(
        "OPENROUTER_EMBEDDING_MODEL",
        DEFAULT_EMBEDDING_MODEL,
    ).strip()

    if not INDEX_CONFIG_FILE.exists():
        return environment_model

    try:
        with open(
            INDEX_CONFIG_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            config = json.load(file)

        indexed_model = _clean_value(
            config.get("model", "")
        )

        return (
            indexed_model
            or environment_model
        )

    except (
        OSError,
        ValueError,
        TypeError,
    ):
        return environment_model


def _metadata_file() -> Path:
    """
    Support both the final production metadata filename and the
    original experimental filename.
    """

    if PRIMARY_METADATA_FILE.exists():
        return PRIMARY_METADATA_FILE

    return LEGACY_METADATA_FILE


def _load_artifacts() -> bool:
    """
    Load the stored NGO embeddings and metadata once.

    Returns False when artifacts are unavailable or invalid.
    The recommender will then use TF-IDF automatically.
    """

    global _ARTIFACTS_LOADED
    global _EMBEDDINGS
    global _METADATA
    global _URL_TO_INDEX
    global _NAME_DISTRICT_TO_INDEX

    if _ARTIFACTS_LOADED:
        return (
            _EMBEDDINGS is not None
            and _METADATA is not None
        )

    with _ARTIFACT_LOCK:

        if _ARTIFACTS_LOADED:
            return (
                _EMBEDDINGS is not None
                and _METADATA is not None
            )

        metadata_file = _metadata_file()

        if (
            not EMBEDDINGS_FILE.exists()
            or not metadata_file.exists()
        ):
            print(
                "Hybrid recommender artifacts are missing. "
                "Falling back to TF-IDF."
            )

            _ARTIFACTS_LOADED = True

            return False

        try:
            embeddings = np.load(
                EMBEDDINGS_FILE
            ).astype(
                np.float32
            )

            metadata = pd.read_csv(
                metadata_file
            ).fillna("")

            if embeddings.ndim != 2:
                raise ValueError(
                    "Embedding file must contain "
                    "a 2D matrix."
                )

            if len(metadata) != len(embeddings):
                raise ValueError(
                    "Embedding and metadata counts "
                    "do not match: "
                    f"{len(embeddings)} embeddings "
                    f"vs {len(metadata)} metadata rows."
                )

            url_to_index: dict[str, int] = {}

            name_district_to_index: dict[
                str,
                int,
            ] = {}

            for index, row in metadata.iterrows():

                url_key = _normalise_url(
                    row.get("url", "")
                )

                if (
                    url_key
                    and url_key not in url_to_index
                ):
                    url_to_index[
                        url_key
                    ] = int(index)

                fallback_key = (
                    _name_district_key(
                        row.get("name", ""),
                        row.get("district", ""),
                    )
                )

                if (
                    fallback_key
                    and fallback_key
                    not in name_district_to_index
                ):
                    name_district_to_index[
                        fallback_key
                    ] = int(index)

            _EMBEDDINGS = embeddings
            _METADATA = metadata

            _URL_TO_INDEX = url_to_index
            _NAME_DISTRICT_TO_INDEX = (
                name_district_to_index
            )

            _ARTIFACTS_LOADED = True

            print(
                "Hybrid recommender loaded: "
                f"{len(embeddings)} NGO embeddings."
            )

            return True

        except Exception as error:
            print(
                "Unable to load hybrid recommender "
                f"artifacts: {error}"
            )

            _ARTIFACTS_LOADED = True
            _EMBEDDINGS = None
            _METADATA = None
            _URL_TO_INDEX = {}
            _NAME_DISTRICT_TO_INDEX = {}

            return False


def _embedding_index_for_ngo(
    ngo: dict[str, Any],
) -> int | None:
    """
    Find the corresponding embedding row for a database NGO.

    URL matching is preferred. Name + district is used as a fallback.
    """

    url_key = _normalise_url(
        ngo.get("url", "")
    )

    if (
        url_key
        and url_key in _URL_TO_INDEX
    ):
        return _URL_TO_INDEX[
            url_key
        ]

    fallback_key = _name_district_key(
        ngo.get("name", ""),
        ngo.get("district", ""),
    )

    if fallback_key:
        return _NAME_DISTRICT_TO_INDEX.get(
            fallback_key
        )

    return None


def _tokenise(text: str) -> list[str]:
    """
    Convert text into lowercase word tokens.
    """

    return TOKEN_PATTERN.findall(
        text.lower()
    )


def _meaningful_query_tokens(
    query: str,
) -> list[str]:
    """
    Extract important domain terms from the user's query.

    Words such as NGO, need, find and support are ignored because
    they are too generic for keyword ranking.
    """

    meaningful_tokens: list[str] = []

    for token in _tokenise(query):

        if token in ENGLISH_STOP_WORDS:
            continue

        if token in GENERIC_QUERY_TERMS:
            continue

        if len(token) <= 2:
            continue

        if token not in meaningful_tokens:
            meaningful_tokens.append(
                token
            )

    return meaningful_tokens


def _keyword_scores(
    query: str,
    documents: list[str],
    vectorizer: TfidfVectorizer,
) -> np.ndarray:
    """
    Calculate exact keyword relevance.

    Rare domain terms receive greater influence using TF-IDF IDF
    values. Consecutive phrase matches receive a small additional
    bonus.

    Keyword relevance contributes only 10% to the final score.
    """

    query_tokens = (
        _meaningful_query_tokens(
            query
        )
    )

    if not query_tokens:
        return np.zeros(
            len(documents),
            dtype=np.float32,
        )

    feature_names = (
        vectorizer
        .get_feature_names_out()
    )

    idf_map = dict(
        zip(
            feature_names,
            vectorizer.idf_,
        )
    )

    query_weights = [
        float(
            idf_map.get(
                token,
                1.0,
            )
        )
        for token in query_tokens
    ]

    total_query_weight = (
        sum(query_weights)
        or 1.0
    )

    query_phrases = [
        (
            f"{query_tokens[index]} "
            f"{query_tokens[index + 1]}"
        )
        for index in range(
            len(query_tokens) - 1
        )
    ]

    scores: list[float] = []

    for document in documents:

        document_lower = (
            document.lower()
        )

        document_tokens = set(
            _tokenise(document)
        )

        matched_weight = sum(
            weight
            for token, weight in zip(
                query_tokens,
                query_weights,
            )
            if token in document_tokens
        )

        token_score = (
            matched_weight
            / total_query_weight
        )

        phrase_score = 0.0

        if query_phrases:

            phrase_matches = sum(
                1
                for phrase in query_phrases
                if phrase in document_lower
            )

            phrase_score = (
                phrase_matches
                / len(query_phrases)
            )

        # Exact token overlap contributes 80%.
        # Exact phrase matching contributes 20%.
        keyword_score = (
            0.80 * token_score
            + 0.20 * phrase_score
        )

        scores.append(
            min(
                1.0,
                keyword_score,
            )
        )

    return np.asarray(
        scores,
        dtype=np.float32,
    )


@lru_cache(maxsize=256)
def _get_query_embedding(
    query: str,
) -> np.ndarray:
    """
    Request one semantic embedding for the user's query.

    Successful repeated queries are cached in memory.
    """

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY "
            "is not configured."
        )

    response = requests.post(
        OPENROUTER_API_URL,
        headers={
            "Authorization": (
                f"Bearer "
                f"{OPENROUTER_API_KEY}"
            ),
            "Content-Type": (
                "application/json"
            ),
        },
        json={
            "model": _embedding_model(),
            "input": query,
        },
        timeout=QUERY_TIMEOUT_SECONDS,
    )

    if not response.ok:
        raise RuntimeError(
            "OpenRouter embedding request "
            f"failed with status "
            f"{response.status_code}: "
            f"{response.text[:300]}"
        )

    body = response.json()
    data = body.get(
        "data",
        [],
    )

    if (
        not data
        or "embedding" not in data[0]
    ):
        raise RuntimeError(
            "OpenRouter returned "
            "no query embedding."
        )

    return np.asarray(
        data[0]["embedding"],
        dtype=np.float32,
    )


def _tfidf_scores(
    query: str,
    documents: list[str],
) -> tuple[
    np.ndarray,
    TfidfVectorizer,
]:
    """
    Calculate TF-IDF cosine similarity for all candidate NGOs.
    """

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
    )

    document_matrix = (
        vectorizer.fit_transform(
            documents
        )
    )

    query_vector = (
        vectorizer.transform(
            [query]
        )
    )

    scores = cosine_similarity(
        query_vector,
        document_matrix,
    ).flatten()

    return (
        scores.astype(
            np.float32
        ),
        vectorizer,
    )


def _hybrid_scores(
    query: str,
    ngos: list[dict[str, Any]],
    documents: list[str],
    tfidf_scores: np.ndarray,
    vectorizer: TfidfVectorizer,
) -> np.ndarray | None:
    """
    Calculate the final production score:

    27% TF-IDF
    63% semantic embedding similarity
    10% keyword relevance
    """

    if (
        not _load_artifacts()
        or _EMBEDDINGS is None
    ):
        return None

    candidate_embedding_indexes = [
        _embedding_index_for_ngo(
            ngo
        )
        for ngo in ngos
    ]

    matched_positions = [
        position
        for position, embedding_index
        in enumerate(
            candidate_embedding_indexes
        )
        if embedding_index is not None
    ]

    if not matched_positions:
        return None

    try:
        query_embedding = (
            _get_query_embedding(
                query.strip()
            )
        )

    except Exception as error:
        print(
            "Hybrid recommender unavailable: "
            f"{error}"
        )

        return None

    if (
        query_embedding.shape[0]
        != _EMBEDDINGS.shape[1]
    ):
        print(
            "Query embedding dimension does not "
            "match stored NGO embeddings. "
            "Falling back to TF-IDF."
        )

        return None

    artifact_indexes = [
        int(
            candidate_embedding_indexes[
                position
            ]
        )
        for position in matched_positions
    ]

    candidate_embeddings = (
        _EMBEDDINGS[
            artifact_indexes
        ]
    )

    raw_embedding_scores = (
        cosine_similarity(
            query_embedding.reshape(
                1,
                -1,
            ),
            candidate_embeddings,
        )
        .flatten()
    )

    # Convert cosine similarity from [-1, 1] to [0, 1],
    # matching the scoring used during experimentation.
    normalised_embedding_scores = (
        np.clip(
            (
                raw_embedding_scores
                + 1.0
            )
            / 2.0,
            0.0,
            1.0,
        )
        .astype(
            np.float32
        )
    )

    keyword_scores = (
        _keyword_scores(
            query,
            documents,
            vectorizer,
        )
    )

    # NGOs without a matched stored embedding retain their
    # TF-IDF score instead of being removed completely.
    final_scores = (
        tfidf_scores.copy()
    )

    for (
        local_index,
        position,
    ) in enumerate(
        matched_positions
    ):

        final_scores[position] = (
            TFIDF_WEIGHT
            * tfidf_scores[position]
            + EMBEDDING_WEIGHT
            * normalised_embedding_scores[
                local_index
            ]
            + KEYWORD_WEIGHT
            * keyword_scores[position]
        )

    return final_scores


def _fetch_ngos(
    district: str = "",
) -> list[dict[str, Any]]:
    """
    Fetch all NGOs and optionally filter them by district.
    """

    data = get_all_ngos(
        page=1,
        per_page=100000,
    )

    if isinstance(data, dict):
        ngos = data.get(
            "results",
            [],
        )

    elif isinstance(data, list):
        ngos = data

    else:
        ngos = []

    cleaned_ngos = [
        dict(ngo)
        for ngo in ngos
        if isinstance(
            ngo,
            dict,
        )
    ]

    if district:

        requested_district = (
            district
            .strip()
            .lower()
        )

        cleaned_ngos = [
            ngo
            for ngo in cleaned_ngos
            if (
                _clean_value(
                    ngo.get(
                        "district",
                        "",
                    )
                )
                .lower()
                == requested_district
            )
        ]

    return cleaned_ngos


def recommend(
    query: str,
    district: str = "",
) -> list[dict[str, Any]]:
    """
    Return the top 10 NGO recommendations.

    Hybrid ranking is used when OpenRouter and the stored embedding
    artifacts are available. TF-IDF is used automatically as a
    fallback when the semantic system is unavailable.
    """

    query = _clean_value(
        query
    )

    district = _clean_value(
        district
    )

    if not query:
        return []

    ngos = _fetch_ngos(
        district
    )

    if not ngos:
        return []

    documents = [
        _build_document(ngo)
        for ngo in ngos
    ]

    try:
        (
            tfidf_scores,
            vectorizer,
        ) = _tfidf_scores(
            query,
            documents,
        )

    except ValueError:
        return []

    final_scores = (
        _hybrid_scores(
            query=query,
            ngos=ngos,
            documents=documents,
            tfidf_scores=tfidf_scores,
            vectorizer=vectorizer,
        )
    )

    # OpenRouter failure, missing API key, missing artifacts,
    # dimension mismatch or other embedding errors all fall
    # back to the working TF-IDF recommender.
    if final_scores is None:
        final_scores = tfidf_scores

    ranked_indexes = (
        np.argsort(
            final_scores
        )[::-1]
    )

    results: list[
        dict[str, Any]
    ] = []

    for index in ranked_indexes:

        score = float(
            final_scores[index]
        )

        if score <= 0:
            continue

        # Copy the complete existing NGO dictionary so the API
        # response structure remains compatible with the frontend.
        result = dict(
            ngos[index]
        )

        result["score"] = round(
            score,
            4,
        )

        results.append(
            result
        )

        if len(results) == TOP_K:
            break

    return results