import csv
import re
from tkinter import simpledialog, messagebox
from connect_db import connect_db
import os

def add_borrower():
    conn = connect_db()
    cursor = conn.cursor()

    def get_new_card_id():
        cursor.execute('SELECT Card_id FROM BORROWER ORDER BY Card_id DESC LIMIT 1')
        last_id = cursor.fetchone()
        num = int(last_id[0][2:])
        return 'ID' + str(num + 1).zfill(6)

    # SSN validation
    ssn_pattern = r'\d{3}-\d{2}-\d{4}'
    while True:
        ssn = simpledialog.askstring("Add Borrower", "Enter SSN (xxx-xx-xxxx):")
        if ssn is None:
            return
        if re.fullmatch(ssn_pattern, ssn):
            break
        messagebox.showerror("Invalid SSN", "❌ Please enter SSN in the format xxx-xx-xxxx.")

    # Check for duplicate SSN
    cursor.execute('SELECT COUNT(*) FROM BORROWER WHERE Ssn=%s', (ssn,))
    if cursor.fetchone()[0] > 0:
        messagebox.showerror("Duplicate SSN", "❌ This SSN is already in use.")
        conn.close()
        return

    name = simpledialog.askstring("Add Borrower", "Enter Full Name:")
    if not name: return

    address = simpledialog.askstring("Add Borrower", "Enter Address:")
    if not address: return

    # Phone validation
    phone_pattern = r'\\d{3}-\d{3}-\d{4}'
    while True:
        phone = simpledialog.askstring("Add Borrower", "Enter Phone ((xxx) xxx-xxxx) or leave blank:")
        if phone in (None, ""):
            phone = None
            break
        if re.fullmatch(phone_pattern, phone):
            break
        messagebox.showerror("Invalid Phone", "❌ Format must be (xxx) xxx-xxxx or blank.")

    new_id = get_new_card_id()

    # Insert into DB
    cursor.execute('INSERT INTO BORROWER VALUES (%s, %s, %s, %s, %s)', (new_id, ssn, name, address, phone))
    conn.commit()
    conn.close()

    # Append to CSV
    csv_path = "library_data/borrower.csv"
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["Card_id", "Ssn", "Bname", "Address", "Phone"])
        writer.writerow([new_id, ssn, name, address, phone or ""])

    messagebox.showinfo("Success", f"✅ Borrower {new_id} added and saved.")

