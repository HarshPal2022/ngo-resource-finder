import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from dotenv import load_dotenv


load_dotenv()


API_URL = "https://openrouter.ai/api/v1/embeddings"

API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = os.getenv(
    "OPENROUTER_EMBEDDING_MODEL",
    "openai/text-embedding-ada-002"
)

CSV_FILE = Path(
    "data/cleaned_ngos.csv"
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

CONFIG_FILE = (
    ARTIFACT_DIR / "index_config.json"
)

DEFAULT_SAMPLE_SIZE = 100

DEFAULT_BATCH_SIZE = 50

MAX_TEXT_CHARS = 6000

MAX_RETRIES = 3


def clean_value(value):
    """
    Convert missing Pandas values into empty strings.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def build_document(row):
    """
    Build the text document used for NGO embeddings.
    """

    purpose = clean_value(
        row.get("purpose", "")
    )

    mission = clean_value(
        row.get("mission", "")
    )

    document = (
        f"Purpose:\n{purpose}\n\n"
        f"Mission:\n{mission}"
    )

    return document[:MAX_TEXT_CHARS]


def request_embeddings(texts):
    """
    Request embeddings from OpenRouter.
    """

    payload = {
        "model": MODEL,
        "input": texts,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(MAX_RETRIES):

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )

        if response.ok:

            body = response.json()

            embedding_data = sorted(
                body["data"],
                key=lambda item: item["index"]
            )

            return [
                item["embedding"]
                for item in embedding_data
            ]

        if response.status_code in {
            429,
            500,
            502,
            503,
            504,
        }:

            wait_seconds = 2 ** attempt

            print(
                f"API error {response.status_code}. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)

            continue

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

    raise RuntimeError(
        "Embedding request failed after retries."
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sample",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=(
            "Number of NGOs to embed. "
            "Use 0 for the complete dataset."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of NGO documents per API request.",
    )

    args = parser.parse_args()

    if not API_KEY:

        raise ValueError(
            "OPENROUTER_API_KEY is missing from .env"
        )

    if not CSV_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found: {CSV_FILE}"
        )

    df = pd.read_csv(
        CSV_FILE
    )

    # Convert all missing values to empty strings.
    # This prevents NaN values from entering
    # the embedding documents or metadata.
    df = df.fillna("")

    print(
        f"Loaded {len(df)} NGOs from dataset."
    )

    if args.sample > 0:

        df = df.head(
            args.sample
        ).copy()

        print(
            f"Using sample of {len(df)} NGOs."
        )

    else:

        df = df.copy()

        print(
            f"Using complete dataset: "
            f"{len(df)} NGOs."
        )

    documents = [
        build_document(row)
        for _, row in df.iterrows()
    ]

    all_embeddings = []

    total = len(documents)

    for start in range(
        0,
        total,
        args.batch_size,
    ):

        end = min(
            start + args.batch_size,
            total,
        )

        batch = documents[
            start:end
        ]

        print(
            f"Embedding {start + 1}-{end} "
            f"of {total}..."
        )

        embeddings = request_embeddings(
            batch
        )

        if len(embeddings) != len(batch):

            raise RuntimeError(
                "Embedding count does not "
                "match input batch size."
            )

        all_embeddings.extend(
            embeddings
        )

        time.sleep(0.5)

    embedding_matrix = np.asarray(
        all_embeddings,
        dtype=np.float32,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save cleaned metadata.
    df.to_csv(
        METADATA_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    # Save embedding matrix.
    np.save(
        EMBEDDINGS_FILE,
        embedding_matrix,
    )

    config = {
        "model": MODEL,
        "count": len(df),
        "dimensions": int(
            embedding_matrix.shape[1]
        ),
        "source": str(CSV_FILE),
    }

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=4,
        )

    print(
        "\nEmbedding index created."
    )

    print(
        f"NGOs: {len(df)}"
    )

    print(
        f"Dimensions: "
        f"{embedding_matrix.shape[1]}"
    )

    print(
        f"Saved: "
        f"{EMBEDDINGS_FILE}"
    )

    print(
        f"Saved: "
        f"{METADATA_FILE}"
    )


if __name__ == "__main__":
    main()