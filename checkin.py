from connect_db import connect_db
from datetime import datetime

def checkin_book(isbn, card_id, name):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    like_name = f"%{name.strip().upper()}%"
    
    # Find active loan
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
    if not loans:
        print("❌ No active loan found for this book and borrower.")
        return
    else:
        print("\nActive Loans:")
        for row in loans:
            print(f"{row['Loan_id']} | {row['ISBN']} | {row['Title']} | {row['Date_out']} | {row['Due_date']}")

    loan_id = input('\nSelect Loan_id to Check In: ')
    today = datetime.today().date()

    # Update loan to mark as returned
    cursor.execute("""
        UPDATE BOOK_LOANS
        SET date_in = %s
        WHERE Loan_id = %s
    """, (today, loan_id))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Book Loan {loan_id} successfully checked in.")

