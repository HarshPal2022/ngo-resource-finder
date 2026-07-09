import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.db import get_all_ngos


def recommend(query, district=""):

    # Fetch all NGOs (ignore pagination for AI)
    data = get_all_ngos(
    page=1,
    per_page=100000
)

    ngos = data["results"]

    if district:
        ngos = [
            ngo for ngo in ngos
            if ngo.get("district")
            and ngo["district"].lower() == district.lower()
        ]

    if not ngos:
        return []

    df = pd.DataFrame(ngos)
    df = df.fillna("")
    df["purpose"] = df["purpose"].fillna("")
    df["mission"] = df["mission"].fillna("")

    df["document"] = (
        df["purpose"].astype(str)
        + " "
        + df["mission"].astype(str)
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000,
    )

    tfidf_matrix = vectorizer.fit_transform(df["document"])

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        tfidf_matrix,
    ).flatten()

    df["score"] = scores

    df = df[df["score"] > 0]

    if df.empty:
        return []

    df = df.sort_values(
        by="score",
        ascending=False,
    ).head(10)

    results = []

    for _, row in df.iterrows():

        results.append({
        "id": int(row["id"]),
        "name": "" if pd.isna(row["name"]) else row["name"],
        "district": "" if pd.isna(row["district"]) else row["district"],
        "address": "" if pd.isna(row["address"]) else row["address"],
        "phone": "" if pd.isna(row["phone"]) else row["phone"],
        "mobile": "" if pd.isna(row["mobile"]) else row["mobile"],
        "email": "" if pd.isna(row["email"]) else row["email"],
        "website": "" if pd.isna(row["website"]) else row["website"],
        "contact_person": "" if pd.isna(row["contact_person"]) else row["contact_person"],
        "purpose": "" if pd.isna(row["purpose"]) else row["purpose"],
        "mission": "" if pd.isna(row["mission"]) else row["mission"],
        "url": "" if pd.isna(row["url"]) else row["url"],
        "score": round(float(row["score"]),4)
        })

    return results