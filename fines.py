from connect_db import connect_db
from datetime import datetime

def update_fines():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    today = datetime.today().date()

    # Get all loans that are late (returned or not)
    cursor.execute("""
        SELECT * FROM BOOK_LOANS
        WHERE (Date_in IS NULL AND Due_date < %s)
           OR (Date_in IS NOT NULL AND Date_in > Due_date)
    """, (today,))

    loans = cursor.fetchall()

    for loan in loans:
        due = loan['Due_date']
        returned = loan['Date_in']
        loan_id = loan['Loan_id']

        if returned:
            days_late = (returned - due).days
        else:
            days_late = (today - due).days

        if days_late > 0:
            fine_amt = days_late * 0.25

            cursor.execute("SELECT * FROM FINES WHERE Loan_id = %s", (loan_id,))
            existing = cursor.fetchone()

            if existing:
                if not existing['Paid']:
                    cursor.execute("UPDATE FINES SET Fine_amt = %s WHERE Loan_id = %s", (fine_amt, loan_id))
            else:
                cursor.execute("""
                    INSERT INTO FINES
                    VALUES (%s, %s, 0)
                """, (loan_id, fine_amt))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Fines updated.")

def pay_fines():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    # Get unpaid fines for returned books
    cursor.execute("""
        SELECT bl.Card_id, SUM(Fine_amt) AS Total_fines
        FROM BOOK_LOANS bl JOIN FINES f ON bl.Loan_id = f.Loan_id
        WHERE Paid = 0 AND bl.Date_in IS NOT NULL
        GROUP BY Card_id
    """)

    fines = cursor.fetchall()

    if not fines:
        print("❌ No fines currently eligible for payment.")
        return
    else:
        print("\nEligibile Fines:")
        for row in fines:
            print(f"{row['Card_id']} | {row['Total_fines']}")

    card_id = input('\nEnter the Borrower Card ID of the Fine to Pay: ')

    #Get all eligible fines by borrower card_id
    cursor.execute("""
        SELECT f.Loan_id
        FROM BOOK_LOANS bl JOIN FINES f ON bl.Loan_id = f.loan_id
        WHERE bl.Card_id = %s AND Paid = 0 AND bl.Date_in IS NOT NULL
    """, (card_id,))
    elg_fines = cursor.fetchall()

    #Update all fines to paid = 1
    for row in elg_fines:
        cursor.execute("""
            UPDATE FINES SET Paid = 1
            WHERE Loan_id = %s
        """, (row['Loan_id'],))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ All eligible fines for Borrower {card_id} have been paid.")

