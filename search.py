import re
from connect_db import connect_db

def normalize_initials(name):
    # Normalize initials to non-space separated format: "J. K." becomes "J.K."
    return re.sub(r'([A-Za-z])\.\s*', r'\1.', name).strip()

def search(query):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    query = query.strip()

    isbn_candidate = None
    title_terms = []
    author_terms = []

    # Split the query into tokens.
    tokens = query.split()

    # Look for a token that looks like an ISBN (digits/hyphens, length 10+)
    for token in tokens:
        token_clean = token.replace(" ", "")
        if all(c.isdigit() or c == '-' for c in token_clean) and len(token_clean) >= 10:
            isbn_candidate = token_clean
            break

    # Remove the ISBN token from further processing.
    filtered_tokens = [token for token in tokens
                       if not (isbn_candidate and token.replace(" ", "") == isbn_candidate)]

    # Check for an explicit " by " separator.
    if " by " in query.lower():
        index = query.lower().find(" by ")
        title_part = query[:index]
        author_part = query[index + 4:]
        title_terms = [term.strip() for term in title_part.split() if term.strip()]
        author_terms = [normalize_initials(term.strip()) for term in author_part.split() if term.strip()]
    else:
        # Use a heuristic: if any token contains a dot, assume that token and all subsequent tokens are author tokens.
        found_author = False
        for token in filtered_tokens:
            if not found_author and '.' in token:
                found_author = True
            if found_author:
                author_terms.append(normalize_initials(token))
            else:
                title_terms.append(token)
        # If no token qualifies as an author, assume all tokens are title tokens.
        if not author_terms:
            title_terms = filtered_tokens

    # Build query conditions.
    conditions = []
    params = []

    # 1. ISBN condition (exact match)
    if isbn_candidate:
        conditions.append("b.Isbn = %s")
        params.append(isbn_candidate)

    # 2. Title condition (exact and fuzzy matching)
    if title_terms:
        title_conditions = []
        for term in title_terms:
            title_conditions.append("(b.Title LIKE %s OR SOUNDEX(b.Title) = SOUNDEX(%s))")
            params.append(f"%{term}%")
            params.append(term)
        # Require all title terms to appear.
        conditions.append("(" + " AND ".join(title_conditions) + ")")

    # 3. Author condition (fuzzy matching)
    if author_terms:
        author_conditions = []
        for term in author_terms:
            author_conditions.append("(a.Name LIKE %s OR SOUNDEX(a.Name) = SOUNDEX(%s))")
            params.append(f"%{term}%")
            params.append(term)
        author_subquery = """
            EXISTS (
                SELECT 1 FROM BOOK_AUTHORS ba 
                JOIN AUTHORS a ON ba.Author_id = a.Author_id 
                WHERE ba.Isbn = b.Isbn AND ({})
            )
        """.format(" AND ".join(author_conditions))
        conditions.append(author_subquery)

    # Combine the conditions with OR so that:
    # - The exact ISBN match is returned if provided.
    # - Books matching the title fuzzy search are returned.
    # - Books matching the author fuzzy search are returned.
    # This produces a union of results.
    where_clause = " OR ".join(conditions) if conditions else "1=0"

    sql = f"""
        SELECT 
            b.Isbn,
            b.Title,
            (SELECT GROUP_CONCAT(DISTINCT a.Name ORDER BY a.Name SEPARATOR ', ')
             FROM BOOK_AUTHORS ba
             JOIN AUTHORS a ON ba.Author_id = a.Author_id
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
    """
    # Append ISBN candidate for ordering if available.
    if isbn_candidate:
        params.append(isbn_candidate)
    else:
        params.append('')

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
