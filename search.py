from connect_db import connect_db

def search(query):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    where_clause = ''

    cursor.execute('SELECT * FROM INFORMATION_SCHEMA.INNODB_FT_DEFAULT_STOPWORD')
    stopwords = cursor.fetchall()

    #If query is only a stopword, do substring matching
    if query.lower() in [row['value'] for row in stopwords]:
        like_query = f"%{query.strip().upper()}%"
        where_clause = f"Title LIKE '{like_query}' OR Authors LIKE '{like_query}'"
    else:
        #Full-text matching
        where_clause = f"""MATCH(Isbn, Title, Authors) AGAINST('{query}' IN NATURAL LANGUAGE MODE) """
    
    cursor.execute(f"""
        SELECT *, 
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM BOOK_LOANS bl, BOOK b
                    WHERE bl.Isbn = b.Isbn AND bl.date_in IS NULL
                ) THEN 'OUT'
                ELSE 'IN'
            END AS Status
        FROM FULL_BOOK
        WHERE {where_clause} 
        LIMIT 50
    """)

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        print("No matching books found.")
        return

    print("\nMatching Books:")
    for i, row in enumerate(results, 1):
        print(f"{i}: {row['Isbn']} | {row['Title']} | {row['Authors']} | {row['Status']}")
