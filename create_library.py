import mysql.connector
import pandas as pd

def main():
    # Connect to MySQL Server
    print("Connecting to MySQL Server...")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password"
    )
    cursor = conn.cursor()
    print("Connected successfully.")

    # Create and use database
    print("Creating database LIBRARY_BORON...")
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute("DROP DATABASE IF EXISTS LIBRARY_BORON")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")

    cursor.execute('CREATE DATABASE LIBRARY_BORON')
    cursor.execute('USE LIBRARY_BORON')
    conn.commit()
    print("Database LIBRARY_BORON created and selected.")

    # Create and load BOOK table
    print("Creating and loading BOOK table...")
    cursor.execute('DROP TABLE IF EXISTS BOOK')
    cursor.execute('''
        CREATE TABLE BOOK (
            Isbn CHAR(10) NOT NULL,
            Title VARCHAR(255) NOT NULL,
            CONSTRAINT BOOKPK PRIMARY KEY (Isbn)
        )
    ''')
    book_data = pd.read_csv('./library_data/book.csv', sep='\t', encoding='utf-8')
    book_values = book_data[['Isbn', 'Title']].values.tolist()
    cursor.executemany('INSERT INTO BOOK VALUES (%s, %s)', book_values)
    conn.commit()
    print(f"Inserted {len(book_values)} records into BOOK table.")

    # Create and load AUTHORS table
    print("Creating and loading AUTHORS table...")
    cursor.execute('DROP TABLE IF EXISTS AUTHORS')
    cursor.execute('''
        CREATE TABLE AUTHORS (
            Author_id INT NOT NULL,
            Name VARCHAR(255) NOT NULL,
            CONSTRAINT AUTHORSPK PRIMARY KEY (Author_id)
        )
    ''')
    authors_data = pd.read_csv('./library_data/authors.csv', encoding='utf-8')
    authors_data['Name'] = authors_data['Name'].astype(str)
    authors_values = authors_data[['Author_id', 'Name']].values.tolist()
    cursor.executemany('INSERT INTO AUTHORS VALUES (%s, %s)', authors_values)
    conn.commit()
    print(f"Inserted {len(authors_values)} records into AUTHORS table.")

    # Create and load BOOK_AUTHORS table
    print("Creating and loading BOOK_AUTHORS table...")
    cursor.execute('DROP TABLE IF EXISTS BOOK_AUTHORS')
    cursor.execute('''
        CREATE TABLE BOOK_AUTHORS (
            Author_id INT NOT NULL,
            Isbn CHAR(10) NOT NULL,
            CONSTRAINT BOOKAUTHPK PRIMARY KEY (Author_id, Isbn),
            CONSTRAINT BA_AUTHORFK FOREIGN KEY (Author_id) REFERENCES AUTHORS(Author_id),
            CONSTRAINT BA_ISBNFK FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn)
        )
    ''')
    bk_authors_data = pd.read_csv('./library_data/book_authors.csv', encoding='utf-8')
    bk_authors_values = bk_authors_data[['Author_id', 'Isbn']].values.tolist()
    cursor.executemany('INSERT IGNORE INTO BOOK_AUTHORS VALUES (%s, %s)', bk_authors_values)
    conn.commit()
    print(f"Inserted {len(bk_authors_values)} records into BOOK_AUTHORS table.")

    # Create and load BORROWER table
    print("Creating and loading BORROWER table...")
    cursor.execute('DROP TABLE IF EXISTS BORROWER')
    cursor.execute('''
        CREATE TABLE BORROWER (
            Card_id CHAR(8) NOT NULL,
            Ssn CHAR(11) NOT NULL,
            Bname VARCHAR(255) NOT NULL,
            Address VARCHAR(255) NOT NULL,
            Phone CHAR(14),
            UNIQUE (Ssn),
            CONSTRAINT BORROWERPK PRIMARY KEY (Card_id)
        )
    ''')
    borrower_data = pd.read_csv('./library_data/borrower.csv', encoding='utf-8')
    borrower_values = borrower_data[['Card_id', 'Ssn', 'Bname', 'Address', 'Phone']].values.tolist()
    cursor.executemany('INSERT INTO BORROWER VALUES (%s, %s, %s, %s, %s)', borrower_values)
    conn.commit()
    print(f"Inserted {len(borrower_values)} records into BORROWER table.")

    # Create BOOK_LOANS table and trigger
    print("Creating BOOK_LOANS table and trigger...")
    cursor.execute('DROP TABLE IF EXISTS BOOK_LOANS')
    cursor.execute('''
        CREATE TABLE BOOK_LOANS (
            Loan_id INT NOT NULL AUTO_INCREMENT,
            Isbn CHAR(10) NOT NULL,
            Card_id CHAR(8) NOT NULL,
            Date_out DATE NOT NULL,
            Due_date DATE NOT NULL,
            Date_in DATE,
            CONSTRAINT LOANSPK PRIMARY KEY (Loan_id),
            CONSTRAINT BL_ISBNFK FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn),
            CONSTRAINT BL_CARDIDFK FOREIGN KEY (Card_id) REFERENCES BORROWER(Card_id)
        )
    ''')
    cursor.execute('DROP TRIGGER IF EXISTS set_due_date')
    cursor.execute('''
        CREATE TRIGGER set_due_date BEFORE INSERT ON BOOK_LOANS
        FOR EACH ROW SET 
            NEW.Date_out = IFNULL(NEW.Date_out, CURRENT_DATE()), 
            NEW.Due_date = DATE_ADD(NEW.Date_out, INTERVAL 14 DAY)
    ''')
    conn.commit()
    print("BOOK_LOANS table and trigger created.")

    # Create FINES table
    print("Creating FINES table...")
    cursor.execute('DROP TABLE IF EXISTS FINES')
    cursor.execute('''
        CREATE TABLE FINES (
            Loan_id INT NOT NULL,
            Fine_amt DEC(5, 2),
            Paid BOOL DEFAULT 0,
            CONSTRAINT FINESPK PRIMARY KEY (Loan_id),
            CONSTRAINT F_LOANIDFK FOREIGN KEY (Loan_id) REFERENCES BOOK_LOANS(Loan_id)
        )
    ''')
    conn.commit()
    print("FINES table created.")

    # Create FULL_BOOK table without index first, then add the full-text index
    print("Creating FULL_BOOK table without full-text index...")
    cursor.execute('DROP TABLE IF EXISTS FULL_BOOK')
    cursor.execute('''
        CREATE TABLE FULL_BOOK AS 
        SELECT 
            b.Isbn, 
            b.Title, 
            GROUP_CONCAT(DISTINCT a.Name ORDER BY a.Name SEPARATOR ', ') AS Authors
        FROM BOOK b 
        JOIN BOOK_AUTHORS ba ON b.Isbn = ba.Isbn
        JOIN AUTHORS a ON ba.Author_id = a.Author_id
        GROUP BY b.Isbn, b.Title
    ''')
    conn.commit()
    print("FULL_BOOK table created. Now adding full-text index...")

    # Add the full-text index in a separate step
    cursor.execute('ALTER TABLE FULL_BOOK ADD FULLTEXT full_book_index(Isbn, Title, Authors)')
    conn.commit()
    print("FULL_BOOK table indexed with full-text index.")

    cursor.close()
    conn.close()
    print("Database setup completed successfully.")

if __name__ == "__main__":
    main()