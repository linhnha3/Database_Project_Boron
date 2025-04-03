from connect_db import connect_db
from datetime import datetime, timedelta

def checkout_book(isbn, card_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    # --- Check if borrower exists ---
    cursor.execute("SELECT * FROM BORROWER WHERE Card_id = %s", (card_id,))
    if not cursor.fetchone():
        print("❌ Borrower not found.")
        return

    # --- Check if book exists ---
    cursor.execute("SELECT * FROM BOOK WHERE Isbn = %s", (isbn,))
    if not cursor.fetchone():
        print("❌ Book not found.")
        return

    # --- Check for unpaid fines ---
    cursor.execute("""
        SELECT * FROM FINES f
        JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
        WHERE bl.card_id = %s AND f.paid = 0
    """, (card_id,))
    if cursor.fetchall():
        print("❌ Borrower has unpaid fines.")
        return

    # --- Check active loan count ---
    cursor.execute("""
        SELECT COUNT(*) AS active_loans FROM BOOK_LOANS
        WHERE card_id = %s AND date_in IS NULL
    """, (card_id,))
    if cursor.fetchone()['active_loans'] == 3:
        print("❌ Borrower already has 3 active loans.")
        return

    # --- Check if book is already checked out ---
    cursor.execute("""
        SELECT * FROM BOOK_LOANS
        WHERE Isbn = %s AND date_in IS NULL
    """, (isbn,))
    if cursor.fetchone():
        print("❌ Book is already checked out.")
        return

    # --- Perform checkout ---
    date_out = datetime.today().date()
    due_date = date_out + timedelta(days=14)

    cursor.execute("""
        INSERT INTO BOOK_LOANS (Isbn, Card_id, Date_out, Due_date, Date_in)
        VALUES (%s, %s, %s, %s, NULL)
    """, (isbn, card_id, date_out, due_date))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Book {isbn} successfully checked out to borrower {card_id}. Due date: {due_date}")

