from connect_db import connect_db

def normalize_initials(name):
    # Normalize initials by ensuring consistent spacing around dots
    name = name.replace('.', '. ').replace('  ', ' ').strip()
    return name

def search(query):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    # Clean and normalize the query
    query = query.strip()

    # Initialize search parameters
    title_terms = []
    author_terms = []
    isbn_search = None

    # Try to detect "by" pattern (title by author)
    if " by " in query.lower():
        parts = query.split(" by ", 1)
        title_terms = [term.strip() for term in parts[0].split() if term.strip()]
        author_terms = [normalize_initials(term.strip()) for term in parts[1].split() if term.strip()]
    else:
        # Check if the query might be an ISBN (digits and hyphens only)
        if all(c.isdigit() or c == '-' for c in query.replace(" ", "")):
            isbn_search = query.replace(" ", "")  # Remove spaces from ISBN
        else:
            # Regular search - treat all terms as potentially title or author
            terms = [term.strip() for term in query.split() if term.strip()]
            title_terms = terms
            author_terms = [normalize_initials(term) for term in terms]

    # Build the SQL query dynamically
    conditions = []
    params = []

    # ISBN search (exact match)
    if isbn_search:
        conditions.append("b.Isbn = %s")
        params.append(isbn_search)

    # Title search (AND logic for all title terms)
    if title_terms:
        title_conditions = []
        for term in title_terms:
            title_conditions.append("b.Title LIKE %s")
            params.append(f"%{term}%")
        conditions.append("(" + " AND ".join(title_conditions) + ")")

    # Author search (special handling for initials)
    if author_terms:
        author_conditions = []
        for term in author_terms:
            # Search both normalized and non-normalized versions
            if '.' in term:  # Likely contains initials
                # Search for both space and non-space separated initials
                normalized_term = normalize_initials(term)
                author_conditions.append("(a.Name LIKE %s OR a.Name LIKE %s)")
                params.append(f"%{term}%")
                params.append(f"%{normalized_term}%")
            else:
                author_conditions.append("a.Name LIKE %s")
                params.append(f"%{term}%")

        author_subquery = """
            EXISTS (
                SELECT 1 FROM BOOK_AUTHORS ba 
                JOIN AUTHORS a ON ba.Author_id = a.Author_id 
                WHERE ba.Isbn = b.Isbn AND ({})
            )
        """.format(" AND ".join(author_conditions))
        conditions.append(author_subquery)

    # Combine conditions with AND if we have both title and author from "by" pattern
    # Otherwise combine with OR for general search
    if title_terms and author_terms and " by " in query.lower():
        where_clause = " AND ".join(conditions)
    else:
        where_clause = " OR ".join(conditions) if conditions else "1=0"

    # Build the final query
    sql = """
        SELECT 
            b.Isbn,
            b.Title,
            (SELECT GROUP_CONCAT(DISTINCT a.Name ORDER BY a.Name SEPARATOR ', ') 
             FROM BOOK_AUTHORS ba JOIN AUTHORS a ON ba.Author_id = a.Author_id 
             WHERE ba.Isbn = b.Isbn) AS Authors,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM BOOK_LOANS bl
                    WHERE bl.Isbn = b.Isbn AND bl.date_in IS NULL
                ) THEN 'OUT'
                ELSE 'IN'
            END AS Status
        FROM BOOK b
        WHERE {where_clause}
        GROUP BY b.Isbn, b.Title
        ORDER BY 
            CASE WHEN b.Isbn = %s THEN 0 ELSE 1 END,
            LENGTH(b.Title)
        LIMIT 50
    """.format(where_clause=where_clause)

    # Add ISBN for exact match ordering if we're doing ISBN search
    if isbn_search:
        params.append(isbn_search)
    else:
        params.append('')  # Empty string for the ISBN match case

    cursor.execute(sql, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        print("No matching books found.")
        return

    print("\nMatching Books:")
    for i, row in enumerate(results, 1):
        print(f"{i}: {row['Isbn']} | {row['Title']} | {row['Authors']} | {row['Status']}")