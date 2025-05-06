from connect_db import connect_db
from datetime import datetime

def checkin_book(isbn, card_id, name):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    like_name = f"%{name.strip().upper()}%"
    
    if isbn != '':
        cursor.execute("""
                SELECT bl.Loan_id, b.Isbn AS ISBN, b.Title, bl.Date_out, bl.Due_date
                FROM BOOK_LOANS bl JOIN BORROWER br ON bl.Card_id = br.Card_id JOIN BOOK b ON bl.Isbn = b.Isbn
                WHERE b.Isbn = %s AND bl.Date_in IS NULL;
            """, (isbn,))
    else:
        cursor.execute("""
                SELECT bl.Loan_id, b.Isbn AS ISBN, b.Title, bl.Date_out, bl.Due_date
                FROM BOOK_LOANS bl JOIN BORROWER br ON bl.Card_id = br.Card_id JOIN BOOK b ON bl.Isbn = b.Isbn
                WHERE (br.Card_id = %s OR br.Bname LIKE %s) AND bl.Date_in IS NULL;
            """, (card_id, like_name))
    
    loans = cursor.fetchall()

    cursor.close()
    conn.close()

    return loans
