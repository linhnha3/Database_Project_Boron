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
        # Extract ISBN Tokens
        tokens = query.split()
        isbn_tokens = []
        for token in tokens:
            cleaned = token.replace("-", "")
            # Assume an ISBN-10 is a token of 10 digits/letters after removing hyphens
            if cleaned.isalnum() and len(cleaned) == 10:
                isbn_tokens.append(token.replace(" ", ""))
        
        #If no ISBNs found, do general search on full query
        if not isbn_tokens:
            where_clause = f"""MATCH(Isbn, Title, Authors) AGAINST('{query}' IN NATURAL LANGUAGE MODE) """
        else:
            #Match by only ISBN(s)
            isbns = ''
            for isbn in isbn_tokens:
                isbns += isbn + " "
            where_clause = f"""MATCH(Isbn, Title, Authors) AGAINST('{isbns}' IN NATURAL LANGUAGE MODE) """
    
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
        LIMIT 100
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