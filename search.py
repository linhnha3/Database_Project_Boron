from connect_db import connect_db

def search(query, return_results=False):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM INFORMATION_SCHEMA.INNODB_FT_DEFAULT_STOPWORD')
    stopwords = [row['value'].lower() for row in cursor.fetchall()]

    # Determine WHERE clause based on query
    query_lower = query.strip().lower()
    where_clause = ""

    if query_lower in stopwords:
        like_query = f"%{query.strip().upper()}%"
        where_clause = f"Title LIKE '{like_query}' OR Authors LIKE '{like_query}'"
    else:
        tokens = query.split()
        isbn_tokens = [t.replace("-", "") for t in tokens if t.replace("-", "").isalnum() and len(t.replace("-", "")) == 10]

        if not isbn_tokens:
            # General full-text search
            where_clause = f"""MATCH(Isbn, Title, Authors) AGAINST('{query}' IN NATURAL LANGUAGE MODE)"""
        else:
            isbns = " ".join(isbn_tokens)
            where_clause = f"""MATCH(Isbn, Title, Authors) AGAINST('{isbns}' IN NATURAL LANGUAGE MODE)"""

    # Execute main query
    cursor.execute(f"""
        SELECT *,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM BOOK_LOANS bl
                    WHERE bl.Isbn = FULL_BOOK.Isbn AND bl.date_in IS NULL
                ) THEN 'OUT'
                ELSE 'IN'
            END AS Status
        FROM FULL_BOOK
        WHERE {where_clause}
        LIMIT 100
    """)

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Behavior split based on return_results
    if return_results:
        return results

    if not results:
        print("No matching books found.")
        return

    print("\nMatching Books:")
    for i, row in enumerate(results, 1):
        print(f"{i}: {row['Isbn']} | {row['Title']} | {row['Authors']} | {row['Status']}")
