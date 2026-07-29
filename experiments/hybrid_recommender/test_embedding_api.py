import os
import requests

from dotenv import load_dotenv


load_dotenv()

API_URL = "https://openrouter.ai/api/v1/embeddings"

API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = os.getenv(
    "OPENROUTER_EMBEDDING_MODEL",
    "openai/text-embedding-ada-002"
)


def main():

    if not API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is missing from .env"
        )

    payload = {
        "model": MODEL,
        "input": (
            "I need education support for girls "
            "and women in rural communities."
        )
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    print("Testing OpenRouter Embeddings...")
    print(f"Model: {MODEL}")

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if not response.ok:

        print("\nOpenRouter returned an error:")
        print(response.status_code)
        print(response.text)

        response.raise_for_status()

    data = response.json()

    embedding = data["data"][0]["embedding"]

    print("\nEmbedding request successful.")
    print(f"Embedding dimensions: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    main()