from connect_db import connect_db
from tkinter import messagebox
from datetime import datetime

# def addTestFines():
#     print("Waow! Adding test fines")
#     conn = connect_db()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("DELETE FROM FINES WHERE Loan_id IN (1, 2, 3, 4)")
#     cursor.execute("DELETE FROM BOOK_LOANS WHERE Loan_id IN (1, 2, 3, 4)")
#     conn.commit()
#     print("Existing test data cleared.")

#     # Test data
#     test_fines = [
#         (1, 5.00),
#         (2, 10.00),
#         (3, 15.00),
#         (4, 20.00),
#     ]
#     test_loans = [
#         (1, '0001047973', 'ID000001', '2023-01-01', '2023-01-15', None),
#         (2, '0001360469', 'ID000002', '2023-01-02', '2023-01-16', None),
#         (3, '0001374869', 'ID000003', '2023-01-03', '2023-01-17', '2023-01-20'),
#         (4, '0001714600', 'ID000004', '2023-01-04', '2023-01-18', '2023-01-18'),
#     ]

#     for fine in test_fines:
#         loan_id, fine_amt = fine
#         print(f"adding test fine into BOOK_LOAN wiht Loan ID {loan_id}")
#         cursor.execute("""
#             INSERT INTO BOOK_LOANS (Loan_id, Isbn, Card_id, Date_out, Due_date, Date_in)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         """, (loan_id,) + test_loans[loan_id - 1][1:])

#         print(f"Adding test fine for Loan ID {loan_id} with amount {fine_amt}")
#         cursor.execute("""
#             INSERT INTO FINES (Loan_id, Fine_amt, Paid)
#             VALUES (%s, %s, 0)
#         """, (loan_id, fine_amt))

#     conn.commit()
#     print("Test fines added to the database.")
#     cursor.close()
#     conn.close()


def update_fines():
    # print("Starting update_fines...")
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    today = datetime.today().date()
    # print(f"Today's date: {today}")

    # Get all loans that are late (returned or not)
    # print("Fetching late loans...")
    cursor.execute("""
        SELECT * FROM BOOK_LOANS
        WHERE (Date_in IS NULL AND Due_date < %s)
           OR (Date_in IS NOT NULL AND Date_in > Due_date)
    """, (today,))
    loans = cursor.fetchall()
    # print(f"Loans fetched: {len(loans)}")

    for loan in loans:
        due = loan['Due_date']
        returned = loan['Date_in']
        loan_id = loan['Loan_id']
        # print(f"Processing Loan ID: {loan_id}, Due Date: {due}, Returned Date: {returned}")

        if returned is None:
            returned = today

        days_late = (returned - due).days
        # print(f"Days late: {days_late}")

        if days_late > 0:
            fine_amt = round(days_late * 0.25, 2)
            # print(f"Calculated fine amount: ${fine_amt}")
            cursor.execute("SELECT * FROM FINES WHERE Loan_id = %s", (loan_id,))
            existing = cursor.fetchone()

            if existing:
                # print(f"Existing fine found for Loan ID {loan_id}: {existing}")
                if not existing['Paid']:
                    # print(f"Updating fine amount for Loan ID {loan_id}")
                    cursor.execute("UPDATE FINES SET Fine_amt = %s WHERE Loan_id = %s", (fine_amt, loan_id))
            else:
                # print(f"Inserting new fine for Loan ID {loan_id}")
                cursor.execute("""
                    INSERT INTO FINES
                    VALUES (%s, %s, 0)
                """, (loan_id, fine_amt))
    conn.commit()
    # print("Fines updated and committed to the database.")
    cursor.close()
    conn.close()

# Pay fines by card_id
def manage_fines(card_id, pay=False):
    # print("Starting manage_fines...")
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    if card_id:
        # print(f"Checking if Card ID {card_id} exists...")
        cursor.execute("SELECT * FROM BORROWER WHERE Card_id = %s", (card_id,))
        borrower = cursor.fetchone()
        if not borrower:
            cursor.close()
            conn.close()
            return f"Invalid Card ID: {card_id}. No such borrower exists."

    # Get total fines due for a borrower
    cursor.execute("""
            SELECT SUM(Fine_amt) AS Total_fines
            FROM BOOK_LOANS bl JOIN FINES f ON bl.Loan_id = f.Loan_id
            WHERE Paid = 0 AND bl.Date_in IS NOT NULL AND Card_id = %s
            GROUP BY Card_id
        """, (card_id,))

    fines = cursor.fetchall()
    if not fines:
        cursor.close()
        conn.close()
        return "No fines currently eligible for payment."

    total_amt = fines[0]['Total_fines']
    pay = messagebox.askyesno("Confirm Payment", f"Pay fine of ${total_amt} for Borrower {card_id}?")
    if not pay:
        cursor.close()
        conn.close()
        return "Payment canceled."

    # If pay is True, proceed to payment
    # Get all eligible fines by borrower card_id
    # print(f"Fetching eligible fines for Card ID {card_id}...")
    cursor.execute("""
        SELECT f.Loan_id
        FROM BOOK_LOANS bl JOIN FINES f ON bl.Loan_id = f.loan_id
        WHERE bl.Card_id = %s AND Paid = 0 AND bl.Date_in IS NOT NULL
    """, (card_id,))
    elg_fines = cursor.fetchall() 
    # print(f"Eligible fines fetched: {len(elg_fines)}")

    # Update all fines to paid = 1
    for row in elg_fines:
        # print(f"Marking fine for Loan ID {row['Loan_id']} as paid...")
        cursor.execute("""
            UPDATE FINES SET Paid = 1
            WHERE Loan_id = %s
        """, (row['Loan_id'],))
    
    conn.commit()
    cursor.close()
    conn.close()

    return f"All eligible fines for Borrower {card_id} have been paid."