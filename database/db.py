import os
import sys

import mysql.connector
import pandas as pd

from database import db_config

CSV_FILE = "data/cleaned_ngos.csv"

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=db_config.MYSQL_HOST,
            port=db_config.MYSQL_PORT,
            user=db_config.MYSQL_USER,
            password=db_config.MYSQL_PASSWORD,
            database=db_config.MYSQL_DATABASE,
        )
        return connection

    except mysql.connector.Error as err:
        print("\nDatabase Connection Failed")
        print(err)
        sys.exit(1)


def insert_data():

    if not os.path.exists(CSV_FILE):
        print(f"\nCSV file not found:\n{CSV_FILE}")
        sys.exit(1)

    df = pd.read_csv(CSV_FILE)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM ngos")

    insert_query = """
    INSERT INTO ngos
    (
        name,
        district,
        address,
        phone,
        mobile,
        email,
        website,
        contact_person,
        purpose,
        mission,
        url
    )
    VALUES
    (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
    )
    """

    inserted = 0

    for _, row in df.iterrows():

        values = (
            None if pd.isna(row["name"]) else str(row["name"]),
            None if pd.isna(row["district"]) else str(row["district"]),
            None if pd.isna(row["address"]) else str(row["address"]),
            None if pd.isna(row["phone"]) else str(row["phone"]),
            None if pd.isna(row["mobile"]) else str(row["mobile"]),
            None if pd.isna(row["email"]) else str(row["email"]),
            None if pd.isna(row["website"]) else str(row["website"]),
            None if pd.isna(row["contact_person"]) else str(row["contact_person"]),
            None if pd.isna(row["purpose"]) else str(row["purpose"]),
            None if pd.isna(row["mission"]) else str(row["mission"]),
            None if pd.isna(row["url"]) else str(row["url"]),
        )

        cursor.execute(insert_query, values)
        inserted += 1

    connection.commit()

    cursor.close()
    connection.close()

    print("=" * 60)
    print("NGOConnect AI - Database Import")
    print("=" * 60)
    print(f"Imported {inserted} NGO records successfully.")


def get_all_ngos():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM ngos
        ORDER BY name
    """)

    ngos = cursor.fetchall()

    cursor.close()
    connection.close()

    return ngos


def get_ngo_by_id(ngo_id):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM ngos
        WHERE id=%s
    """, (ngo_id,))

    ngo = cursor.fetchone()
    cursor.close()
    connection.close()

    return ngo


def get_districts():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT district
        FROM ngos
        ORDER BY district
    """)
    districts = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()
    return districts


def search_ngos(keyword="", district=""):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    keyword = f"%{keyword}%"
    query = """
    SELECT *
    FROM ngos
    WHERE
    (
        name LIKE %s
        OR address LIKE %s
        OR purpose LIKE %s
        OR mission LIKE %s
        OR contact_person LIKE %s
    )
    """

    params = [
        keyword,
        keyword,
        keyword,
        keyword,
        keyword,
    ]

    if district:
        query += " AND district=%s"
        params.append(district)

    query += " ORDER BY name"

    cursor.execute(query, tuple(params))
    ngos = cursor.fetchall()
    cursor.close()
    connection.close()
    return ngos


def count_ngos():

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM ngos")
    count = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return count


def recommend_ngos(ids):
    if not ids:
        return []

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(ids))

    cursor.execute(
        f"""
        SELECT *
        FROM ngos
        WHERE id IN ({placeholders})
        """,
        tuple(ids),
    )
    ngos = cursor.fetchall()
    ngo_map = {ngo["id"]: ngo for ngo in ngos}
    ordered = []

    for ngo_id in ids:
        if ngo_id in ngo_map:
            ordered.append(ngo_map[ngo_id])

    cursor.close()
    connection.close()
    return ordered

if __name__ == "__main__":

    print("=" * 60)
    print("NGOConnect AI - Database Loader")
    print("=" * 60)
    insert_data()
    print(f"Database now contains {count_ngos()} NGOs.")