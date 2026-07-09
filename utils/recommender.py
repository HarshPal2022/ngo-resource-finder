import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.db import get_all_ngos


def recommend(query, district=""):

    ngos = get_all_ngos()

    if district:
        ngos = [
            ngo for ngo in ngos
            if ngo["district"] and ngo["district"].lower() == district.lower()
        ]

    if len(ngos) == 0:
        return []

    df = pd.DataFrame(ngos)

    df["purpose"] = df["purpose"].fillna("")
    df["mission"] = df["mission"].fillna("")

    df["document"] = (
        df["purpose"]
        + " "
        + df["mission"]
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )

    tfidf_matrix = vectorizer.fit_transform(df["document"])

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        tfidf_matrix
    ).flatten()

    df["score"] = scores

    df = df[df["score"] > 0]

    df = df.sort_values(
        by="score",
        ascending=False
    ).head(10)

    results = []

    for _, row in df.iterrows():

        results.append({
            "id": int(row["id"]),
            "name": row["name"],
            "district": row["district"],
            "address": row["address"],
            "phone": row["phone"],
            "mobile": row["mobile"],
            "email": row["email"],
            "website": row["website"],
            "contact_person": row["contact_person"],
            "purpose": row["purpose"],
            "mission": row["mission"],
            "url": row["url"],
            "score": round(float(row["score"]), 4)
        })

    return results