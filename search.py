import re
from connect_db import connect_db


def normalize_initials(name):
    # Normalize initials to a non-space separated format (e.g. "J. K." becomes "J.K.")
    return re.sub(r'([A-Za-z])\.\s*', r'\1.', name).strip()


def search(query):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    query = query.strip()

    # Extract ISBN Tokens
    tokens = query.split()
    isbn_tokens = []
    non_isbn_tokens = []
    for token in tokens:
        cleaned = token.replace("-", "")
        # Assume an ISBN-10 is a token of 10 digits after removing hyphens
        if cleaned.isdigit() and len(cleaned) == 10:
            isbn_tokens.append(token.replace(" ", ""))
        else:
            non_isbn_tokens.append(token)

    # Normalize non-ISBN tokens (e.g. "J. K." -> "J.K.")
    non_isbn_tokens = [normalize_initials(token) for token in non_isbn_tokens]

    # We want to return a book if it matches any of:
    #   a) its ISBN is one of the provided tokens,
    #   b) its title matches at least one non-ISBN token,
    #   c) one of its authors matches at least one non-ISBN token.
    where_clauses = []
    params = []

    if isbn_tokens:
        placeholders = ", ".join(["%s"] * len(isbn_tokens))
        isbn_condition = f"b.Isbn IN ({placeholders})"
        where_clauses.append(isbn_condition)
        params.extend(isbn_tokens)

    # Fuzzy matching on title: check if the title contains any non-ISBN token.
    if non_isbn_tokens:
        title_fuzzy = " OR ".join(["b.Title LIKE %s" for _ in non_isbn_tokens])
        where_clauses.append(f"({title_fuzzy})")
        for token in non_isbn_tokens:
            params.append(f"%{token}%")

        # Fuzzy matching on authors: using a subquery so we don't join AUTHORS directly.
        author_fuzzy = " OR ".join(["a.Name LIKE %s" for _ in non_isbn_tokens])
        author_subquery = f"""
            EXISTS (
                SELECT 1 FROM BOOK_AUTHORS ba
                JOIN AUTHORS a ON ba.Author_id = a.Author_id
                WHERE ba.Isbn = b.Isbn AND ({author_fuzzy})
            )
        """
        where_clauses.append(author_subquery)
        for token in non_isbn_tokens:
            params.append(f"%{token}%")

    # Combine all fuzzy conditions with OR so that if any condition holds, the book is returned.
    if where_clauses:
        overall_where = " OR ".join(f"({wc})" for wc in where_clauses)
    else:
        overall_where = "1=1"

    #  Build the Match Score Expression
    # (a) ISBN bonus: 100 points if the book’s ISBN is among the provided tokens.
    if isbn_tokens:
        placeholders = ", ".join(["%s"] * len(isbn_tokens))
        isbn_bonus = f"CASE WHEN b.Isbn IN ({placeholders}) THEN 100 ELSE 0 END"
        # We'll add the same ISBN tokens for the scoring expression.
        isbn_bonus_params = isbn_tokens.copy()
    else:
        isbn_bonus = "0"
        isbn_bonus_params = []

    # (b) Title score: For each non-ISBN token, add 1 point if b.Title matches.
    title_score_expr = ""
    title_score_params = []
    if non_isbn_tokens:
        title_score_parts = []
        for token in non_isbn_tokens:
            title_score_parts.append("CASE WHEN b.Title LIKE %s THEN 1 ELSE 0 END")
            title_score_params.append(f"%{token}%")
        title_score_expr = " + ".join(title_score_parts)
    else:
        title_score_expr = "0"

    # (c) Author score: Use a subquery to sum points for each non-ISBN token match in any author.
    author_score_expr = ""
    author_score_params = []
    if non_isbn_tokens:
        # For each token, we sum up a CASE over the authors.
        author_score_parts = []
        for token in non_isbn_tokens:
            author_score_parts.append(
                "(SELECT COALESCE(SUM(CASE WHEN a.Name LIKE %s THEN 1 ELSE 0 END), 0) FROM BOOK_AUTHORS ba JOIN AUTHORS a ON ba.Author_id = a.Author_id WHERE ba.Isbn = b.Isbn)"
            )
            author_score_params.append(f"%{token}%")
        author_score_expr = " + ".join(author_score_parts)
    else:
        author_score_expr = "0"

    match_score_expr = f"({isbn_bonus} + {title_score_expr} + {author_score_expr})"

    # Combine all parameters in order
    all_params = params + isbn_bonus_params + title_score_params + author_score_params

    # Build Final SQL Query
    sql = f"""
        SELECT 
            b.Isbn,
            b.Title,
            (SELECT GROUP_CONCAT(DISTINCT a.Name ORDER BY a.Name SEPARATOR ', ')
             FROM BOOK_AUTHORS ba 
             JOIN AUTHORS a ON ba.Author_id = a.Author_id 
             WHERE ba.Isbn = b.Isbn) AS Authors,
            {match_score_expr} AS match_score,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM BOOK_LOANS bl
                    WHERE bl.Isbn = b.Isbn AND bl.date_in IS NULL
                ) THEN 'OUT'
                ELSE 'IN'
            END AS Status
        FROM BOOK b
        WHERE {overall_where}
        GROUP BY b.Isbn, b.Title
        HAVING match_score >= 2
        ORDER BY match_score DESC, LENGTH(b.Title)
    """

    cursor.execute(sql, all_params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        print("No matching books found.")
        return

    # Should return results directly but for now we print.
    print("\nMatching Books:")
    for i, row in enumerate(results, 1):
        print(f"{i}: {row['Isbn']} | {row['Title']} | {row['Authors']} | {row['Status']} (Score: {row['match_score']})")

