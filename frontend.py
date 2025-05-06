import tkinter as tk
from tkinter import simpledialog, messagebox
from connect_db import connect_db
from datetime import datetime
from search import search
from checkout import checkout_book
from checkin import checkin_book   
from fines import update_fines, pay_fines
from borrower import add_borrower


def show_large_popup(title, text):
    popup = tk.Toplevel()
    popup.title(title)
    popup.geometry("800x600")

    text_widget = tk.Text(popup, wrap="word")
    text_widget.insert("1.0", text)
    text_widget.config(state="disabled")  # Make text read-only
    text_widget.pack(expand=True, fill="both")

    close_button = tk.Button(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=5)

def search_books():
    query = simpledialog.askstring("Search Books", "Enter search term (ISBN, Title, or Author):")
    if query:
        results = search(query, return_results=True)
        if not results:
            messagebox.showinfo("Results", "No matching books found.")
            return

        result_text = "Matching Books:\n"
        for i, row in enumerate(results, 1):
            result_text += f"{i}: {row['Isbn']} | {row['Title']} | {row['Authors']} | {row['Status']}\n"

        show_large_popup("Search Results", result_text)

def checkout_book_gui():
    update_fines()
    isbn = simpledialog.askstring("Checkout Book", "Enter ISBN to Check Out:")
    card_id = simpledialog.askstring("Checkout Book", "Enter Borrower's Card ID:")
    if isbn and card_id:
        checkout_book(isbn, card_id)
        messagebox.showinfo("Checkout", "Checkout successful (or see terminal for errors).")

def checkin_book_gui():
    isbn = simpledialog.askstring("Checkin Book", "Enter ISBN to Check In (or leave blank):")
    card_id = simpledialog.askstring("Checkin Book", "Enter Borrower's Card ID (or leave blank):")
    name = simpledialog.askstring("Checkin Book", "Enter Borrower Name (or leave blank):")
    checkin_book(isbn, card_id, name)
    messagebox.showinfo("Checkin", "Checkin successful (or see terminal for errors).")

def pay_fines_gui():
    update_fines()
    pay_fines()
    messagebox.showinfo("Pay Fines", "Fines updated and payment complete (or see terminal for details).")

def add_borrower_gui():
    add_borrower()
    messagebox.showinfo("Add Borrower", "Borrower added successfully (or see terminal for errors).")

def checkin_book_gui():
    isbn = simpledialog.askstring("Checkin Book", "Enter ISBN to Check In (or leave blank):")
    card_id = simpledialog.askstring("Checkin Book", "Enter Borrower's Card ID (or leave blank):")
    name = simpledialog.askstring("Checkin Book", "Enter Borrower Name (or leave blank):")

    loans = checkin_book(isbn, card_id, name)

    if not loans:
        messagebox.showinfo("Checkin", "❌ No active loan found for this book and borrower.")
        return

    # Prepare loan options
    loan_options = []
    for loan in loans:
        desc = f"Loan {loan['Loan_id']} | {loan['ISBN']} | {loan['Title']} | Out: {loan['Date_out']} | Due: {loan['Due_date']}"
        loan_options.append((loan['Loan_id'], desc))

    # Let user pick a loan
    selection_popup = tk.Toplevel()
    selection_popup.title("Select Loan to Check In")
    selection_popup.geometry("700x400")

    var = tk.StringVar(value=loan_options[0][0])  # Default selection is first Loan_id

    for loan_id, desc in loan_options:
        tk.Radiobutton(selection_popup, text=desc, variable=var, value=loan_id).pack(anchor="w", pady=2)

    def confirm_selection():
        selected_loan_id = var.get()
        if selected_loan_id:
            confirm_checkin(selected_loan_id)
            selection_popup.destroy()

    confirm_button = tk.Button(selection_popup, text="Confirm Checkin", command=confirm_selection)
    confirm_button.pack(pady=10)

def confirm_checkin(loan_id):
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.today().date()

    cursor.execute("""
        UPDATE BOOK_LOANS
        SET date_in = %s
        WHERE Loan_id = %s
    """, (today, loan_id))

    conn.commit()
    cursor.close()
    conn.close()

    messagebox.showinfo("Checkin", f"✅ Book Loan {loan_id} successfully checked in!")


def main():
    root = tk.Tk()
    root.title("\ud83d\udcda Library Management System \ud83d\udcda")
    root.geometry("450x550")

    title_label = tk.Label(root, text="Welcome to Library System", font=("Arial", 20))
    title_label.pack(pady=20)

    # Define buttons and actions
    actions = [
        ("\ud83d\udd0d Search Books", search_books),
        ("\ud83d\udcd6 Checkout Book", checkout_book_gui),
        ("\ud83d\udce5 Checkin Book", checkin_book_gui),
        ("\ud83d\udcb5 Pay Fines", pay_fines_gui),
        ("\u2795 Add Borrower", add_borrower_gui),
        ("\ud83d\udeaa Exit", root.quit)
    ]

    for (text, command) in actions:
        btn = tk.Button(root, text=text, command=command, width=30, height=2)
        btn.pack(pady=8)

    root.mainloop()

if __name__ == "__main__":
    main()