from connect_db import connect_db

def search(query):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    like_query = f"%{query.strip().upper()}%"

    cursor.execute("""
        SELECT 
            b.Isbn,
            b.Title,
            GROUP_CONCAT(DISTINCT a.Name ORDER BY a.Name SEPARATOR ', ') AS Authors,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM BOOK_LOANS bl
                    WHERE bl.Isbn = b.Isbn AND bl.date_in IS NULL
                ) THEN 'OUT'
                ELSE 'IN'
            END AS Status
        FROM BOOK b
        JOIN BOOK_AUTHORS ba ON b.Isbn = ba.Isbn
        JOIN AUTHORS a ON ba.Author_id = a.Author_id
        GROUP BY b.Isbn, b.Title
        HAVING 
            LOCATE(b.Isbn, %s) > 0 OR 
            b.Title LIKE %s OR 
            Authors LIKE %s
    """, (query, like_query, like_query))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        print("No matching books found.")
        return

    print("\nMatching Books:")
    for i, row in enumerate(results, 1):
        print(f"{i}: {row['Isbn']} | {row['Title']} | {row['Authors']} | {row['Status']}")
