CS 4347.501 Library System Programming Project
Team Boron
David Wu, Christopher Lau, Vincent Phan, Linh Tran, Khanh Doan, Ross Richards

Files:
    1. normalize.py
        - Normalizes data from books.csv and borrowers.csv
    2. create_library.py
        - Creates MySQL database and loads normalized data from book.csv, borrower.csv, authors.csv, and book_authors.csv into tables
    3. main.py 
        - Main library management system interface for running all functionalities
    4. connect_db.py
        - Contains method for connecting to MySQL database
    5. borrower.py: Add new borrower
    6. checkin.py: Check in books
    7. checkout.py: Check out books
    8. fines.py: Update and pay fines
    9. search.py: Search for books

Required Imports and Terminal Install Commands:
    1. Pandas: pip install Pandas
    2. MySQL Connector: pip install mysql-connector-python

How to Run (in Terminal):
    1. The normalized data is already included in this folder. Running normalize.py will write over the files with the same data.
        - Command: python normalize.py
    2. In connect_db.py and create_library.py, edit 'password' to your actual MySQL root password.
    3. Create and load the database first.
        - Command: python create_library.py
        - Running create_library.py again will reset the database to its original state (with initial data).
    4. Run main.py to access all library system options.
        - Command: python main.py