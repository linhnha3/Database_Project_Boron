from connect_db import connect_db
from datetime import datetime

def checkin_book(isbn, card_id, name):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    where_clause = ''
    
    # Find active loan by given input
    if isbn != '':
        where_clause = f"b.Isbn = {isbn} AND bl.Date_in IS NULL"
    elif card_id != '':
        where_clause = f"br.Card_id = '{card_id}' AND bl.Date_in IS NULL"
    elif name != '':
        like_name = f"%{name.strip().upper()}%"
        where_clause = f"br.Bname LIKE '{like_name}' AND bl.Date_in IS NULL"
    else:
        return "Error: No input given."

    # Get all book loans 
    cursor.execute(f"""
                SELECT bl.Loan_id, b.Isbn AS ISBN, b.Title, bl.Date_out, bl.Due_date
                FROM BOOK_LOANS bl JOIN BORROWER br ON bl.Card_id = br.Card_id JOIN BOOK b ON bl.Isbn = b.Isbn
                WHERE {where_clause}
            """)

    loans = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return loans

