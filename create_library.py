import mysql.connector
import pandas as pd

#Connect to MySQL Server
conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password"
    )
cursor = conn.cursor()

#CREATE and USE database
cursor.execute('DROP DATABASE IF EXISTS LIBRARY_BORON')
cursor.execute('CREATE DATABASE LIBRARY_BORON')
cursor.execute('USE LIBRARY_BORON')
conn.commit()

#CREATE and LOAD BOOK Table
cursor.execute('DROP TABLE IF EXISTS BOOK')
cursor.execute('''CREATE TABLE BOOK (
                    Isbn CHAR(10) NOT NULL,
                    Title VARCHAR(255) NOT NULL,
                    CONSTRAINT BOOKPK PRIMARY KEY (Isbn))
               ''')

book_data = pd.read_csv('book.csv', sep='\t', encoding='utf-8')
for _, row in book_data.iterrows():
    val = (row['Isbn'], row['Title'])
    cursor.execute('INSERT INTO BOOK VALUES (%s, %s)', val)
conn.commit()

#CREATE and LOAD AUTHORS Table
cursor.execute('DROP TABLE IF EXISTS AUTHORS')
cursor.execute('''CREATE TABLE AUTHORS (
                    Author_id INT NOT NULL,
                    Name VARCHAR(255) NOT NULL,
                    CONSTRAINT AUTHORSPK PRIMARY KEY (Author_id))
               ''')

authors_data = pd.read_csv('authors.csv', encoding='utf-8')
for _, row in authors_data.iterrows():
    val = (row['Author_id'], str(row['Name']))
    cursor.execute('INSERT INTO AUTHORS VALUES (%s, %s)', val)
conn.commit()


#CREATE and LOAD BOOK_AUTHORS Table
cursor.execute('DROP TABLE IF EXISTS BOOK_AUTHORS')
cursor.execute('''CREATE TABLE BOOK_AUTHORS (
                    Author_id INT NOT NULL,
                    Isbn CHAR(10) NOT NULL,
                    CONSTRAINT BOOKAUTHPK PRIMARY KEY (Author_id, Isbn),
                    CONSTRAINT BA_AUTHORFK FOREIGN KEY (Author_id) REFERENCES AUTHORS(Author_id),
                    CONSTRAINT BA_ISBNFK FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn))
               ''')

bk_authors_data = pd.read_csv('book_authors.csv', encoding='utf-8')
for _, row in bk_authors_data.iterrows():
    val = (row['Author_id'], row['Isbn'])
    cursor.execute('INSERT IGNORE INTO BOOK_AUTHORS VALUES (%s, %s)', val)
conn.commit()

#CREATE and LOAD BORROWER Table
cursor.execute('DROP TABLE IF EXISTS BORROWER')
cursor.execute('''CREATE TABLE BORROWER (
                    Card_id CHAR(8) NOT NULL,
                    Ssn CHAR(11) NOT NULL,
                    Bname VARCHAR(255) NOT NULL,
                    Address VARCHAR(255) NOT NULL,
                    Phone CHAR(14),
                    UNIQUE (Ssn),
                    CONSTRAINT BORROWERPK PRIMARY KEY (Card_id))
               ''')

borrower_data = pd.read_csv('borrower.csv', encoding='utf-8')
for _, row in borrower_data.iterrows():
    val = (row['Card_id'], row['Ssn'], row['Bname'], row['Address'], row['Phone'])
    cursor.execute('INSERT INTO BORROWER VALUES (%s, %s, %s, %s, %s)', val)
conn.commit()

#CREATE BOOK_LOANS Table
cursor.execute('DROP TABLE IF EXISTS BOOK_LOANS')
cursor.execute('''CREATE TABLE BOOK_LOANS (
                    Loan_id INT NOT NULL AUTO_INCREMENT,
                    Isbn CHAR(10) NOT NULL,
                    Card_id CHAR(8) NOT NULL,
                    Date_out DATE NOT NULL,
                    Due_date DATE NOT NULL,
                    Date_in DATE,
                    CONSTRAINT LOANSPK PRIMARY KEY (Loan_id),
                    CONSTRAINT BL_ISBNFK FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn),
                    CONSTRAINT BL_CARDIDFK FOREIGN KEY (Card_id) REFERENCES BORROWER(Card_id))
               ''')

#TRIGGER: sets date_out to inputted date or current date & due_date to 14 days after date_out
cursor.execute('DROP TRIGGER IF EXISTS set_due_date')
cursor.execute('''CREATE TRIGGER set_due_date BEFORE INSERT ON BOOK_LOANS
                  FOR EACH ROW SET 
                    NEW.Date_out=IFNULL(NEW.Date_out, CURRENT_DATE()), 
                    NEW.Due_date=DATE_ADD(NEW.Date_out, INTERVAL 14 DAY)
               ''')
conn.commit()

#CREATE FINES Table
cursor.execute('DROP TABLE IF EXISTS FINES')
cursor.execute('''CREATE TABLE FINES (
                    Loan_id INT NOT NULL,
                    Fine_amt DEC(5, 2),
                    Paid BOOL DEFAULT 0,
                    CONSTRAINT FINESPK PRIMARY KEY (Loan_id),
                    CONSTRAINT F_LOANIDFK FOREIGN KEY (Loan_id) REFERENCES BOOK_LOANS(Loan_id))
               ''')
conn.commit()

conn.close()