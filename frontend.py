import tkinter as tk
from tkinter import simpledialog, messagebox, Canvas, Scrollbar, Frame
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

""" Deprecated method
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
"""


def get_book_status(isbn):
    """
    Checks if a book is currently available or checked out by querying BOOK_LOANS.
    Returns "Available" or "Checked Out"
    """
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        # Check for an active loan (date_in IS NULL)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
                    SELECT Card_id FROM BOOK_LOANS
                    WHERE Isbn = %s AND date_in IS NULL
                    LIMIT 1
                """, (isbn,))

        loan_record = cursor.fetchone()

        if loan_record:
            # Book has an active loan
            return {"status": "Checked Out", "borrower_id": loan_record['Card_id']}
        else:
            # No active loan found for this ISBN
            return {"status": "Available", "borrower_id": None}

    except Exception as e:
        print(f"Database error in get_book_status_and_borrower for ISBN {isbn}: {e}")
        # Log error appropriately
        return {"status": "Status Unknown", "borrower_id": None}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():  # Check if connection was successful and is still open
            conn.close()

def checkout_from_search_gui(isbn, parent_window, refresh_callback=None):  # Added refresh_callback
    """
    Handles the checkout process initiated from the search results window.
    Prompts for Card ID, calls the main checkout_book function,
    and then calls the refresh_callback if provided and checkout was successful.
    """
    # Adapted from existing checkout method.
    update_fines()
    card_id = simpledialog.askstring("Checkout Book",
                                     f"Enter Borrower's Card ID for ISBN: {isbn}",
                                     parent=parent_window)

    needs_refresh = False
    if card_id:  # Proceed if a Card ID was entered
        result_message = checkout_book(isbn, card_id)  # This is your backend checkout logic
        messagebox.showinfo("Checkout Status", result_message, parent=parent_window)
        # Should consider a more robust method for determining successes
        if "✅" in result_message or "successfully checked out" in result_message.lower():
            needs_refresh = True

    elif card_id == "":  # User pressed OK but left the Card ID field empty
        messagebox.showwarning("Input Error", "Card ID cannot be empty.", parent=parent_window)
    # If card_id is None (user pressed Cancel), do nothing specific for refresh.

    if needs_refresh and refresh_callback:
        print("Refreshing search results...")  # For debugging
        refresh_callback()


def search_books_with_checkout():
    """
    Prompts for a search term, displays results (fetching status separately)
    in a new window with an option to checkout available books.
    """
    # Prompt for the initial search query
    search_query_dialog_val = simpledialog.askstring("Search Books", "Enter search term (ISBN, Title, or Author):")
    if not search_query_dialog_val:
        return  # User cancelled or entered nothing

    current_search_query_holder = [search_query_dialog_val]

    results_window = tk.Toplevel()
    results_window.title("Search Results")
    results_window.geometry("1100x600")

    main_frame = Frame(results_window)
    main_frame.pack(fill=tk.BOTH, expand=True)

    canvas = Canvas(main_frame)
    scrollbar = Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)

    content_frame = Frame(canvas)
    content_frame_window_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def do_populate_or_refresh_results():
        current_query = current_search_query_holder[0]

        # Clear previous results from content_frame
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Re-add headers
        header_bg = "lightgrey"
        header_font = ('Arial', 10, 'bold')
        header_frame_rf = Frame(content_frame, bg=header_bg)
        header_frame_rf.pack(fill="x", pady=(0, 5))
        tk.Label(header_frame_rf, text="ISBN", width=15, font=header_font, anchor="w", bg=header_bg).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Label(header_frame_rf, text="Title", width=35, font=header_font, anchor="w", bg=header_bg).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Label(header_frame_rf, text="Authors", width=30, font=header_font, anchor="w", bg=header_bg).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Label(header_frame_rf, text="Status", width=12, font=header_font, anchor="w", bg=header_bg).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Label(header_frame_rf, text="Borrower ID", width=12, font=header_font, anchor="w", bg=header_bg).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Label(header_frame_rf, text="Action", width=15, font=header_font, anchor="w", bg=header_bg).pack(side=tk.LEFT, padx=5, pady=2)

        initial_results = search(current_query, return_results=True)

        if not initial_results:
            tk.Label(content_frame, text=f"No matching books found for query: '{current_query}'").pack(pady=10)
            content_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
            return

        # Process results (get status for each book)
        processed_results_rf = []
        for book_row in initial_results:
            isbn = book_row.get('Isbn')
            if isbn:
                status = get_book_status(isbn)
                book_row['computed_status'] = status['status']
                book_row['borrower_id'] = status['borrower_id']
            else:
                book_row['computed_status'] = "ISBN Missing"
                book_row['borrower_id'] = None
            processed_results_rf.append(book_row)

        # Display new results
        for row_data in processed_results_rf:
            book_entry_frame_rf = Frame(content_frame)
            book_entry_frame_rf.pack(fill="x", pady=2, padx=2)
            # Add labels for ISBN, Title, Authors
            tk.Label(book_entry_frame_rf, text=row_data.get('Isbn', 'N/A'), width=15, anchor="w").pack(side=tk.LEFT,padx=5)
            tk.Label(book_entry_frame_rf, text=row_data.get('Title', 'N/A'), width=35, anchor="w", wraplength=220).pack(side=tk.LEFT, padx=5)
            tk.Label(book_entry_frame_rf, text=row_data.get('Authors', 'N/A'), width=30, anchor="w",wraplength=180).pack(side=tk.LEFT, padx=5)
            tk.Label(book_entry_frame_rf, text=row_data.get('computed_status', 'N/A'), width=12, anchor="w").pack(side=tk.LEFT, padx=5)

            # Display Borrower ID if book is checked out
            borrower_display_text = ""
            if row_data.get('computed_status') == "Checked Out":
                borrower_display_text = row_data.get('borrower_id', 'N/A')
            tk.Label(book_entry_frame_rf, text=borrower_display_text, width=12, anchor="w").pack(side=tk.LEFT, padx=5)

            action_frame_rf = Frame(book_entry_frame_rf, width=110)
            action_frame_rf.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

            # For anyone curious, this is how I implemented the checkout.
            if row_data.get('computed_status', '').lower() == 'available':
                checkout_button_rf = tk.Button(action_frame_rf, text="Checkout",
                                               command=lambda isbn_val=row_data.get('Isbn'):
                                               checkout_from_search_gui(isbn_val, results_window,
                                                                        do_populate_or_refresh_results))
                checkout_button_rf.pack(anchor="w")
            else:
                tk.Label(action_frame_rf, text="", width=10).pack(anchor="w")

        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    # Initial population of search results
    do_populate_or_refresh_results()

    def on_canvas_configure(event):
        canvas_width = event.width
        canvas.itemconfig(content_frame_window_id, width=canvas_width)
        canvas.config(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", on_canvas_configure)

    def on_content_frame_configure(event):
        canvas.config(scrollregion=canvas.bbox("all"))

    content_frame.bind("<Configure>", on_content_frame_configure)

    results_window.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    close_button = tk.Button(results_window, text="Close", command=results_window.destroy)
    close_button.pack(pady=10)


def checkout_book_gui():
    update_fines()
    isbn = simpledialog.askstring("Checkout Book", "Enter ISBN to Check Out:")
    card_id = simpledialog.askstring("Checkout Book", "Enter Borrower's Card ID:")
    if isbn and card_id:
        checkout_book(isbn, card_id)
        messagebox.showinfo("Checkout", "Checkout successful (or see terminal for errors).")

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
        messagebox.showinfo("Checkin", "No active loan found for this book or borrower.")
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

    messagebox.showinfo("Checkin", f"Book Loan {loan_id} successfully checked in!")


def main():
    root = tk.Tk()
    root.title("\ud83d\udcda Library Management System \ud83d\udcda")
    root.geometry("450x550")

    title_label = tk.Label(root, text="Welcome to Library System", font=("Arial", 20))
    title_label.pack(pady=20)

    # Define buttons and actions
    actions = [
        ("\ud83d\udd0d Search Books", search_books_with_checkout),
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