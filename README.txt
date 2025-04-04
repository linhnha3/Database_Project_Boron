CS 4347.501 Library System Programming Project
Team Boron
David Wu, Christopher Lau, Vincent Phan, Linh Tran, Khanh Doan, Ross Richards

Files:

    1. library_data folder
        - Contains original data files and normalized data files used for creating and loading database
    2. normalize.py
        - Normalizes data from books.csv and borrowers.csv
    3. create_library.py
        - Creates MySQL database and loads normalized data from book.csv, borrower.csv, authors.csv, and book_authors.csv into tables
    4. main.py 
        - Main library management system interface for running all functionalities
    5. connect_db.py
        - Contains method for connecting to MySQL database
    6. borrower.py: Add new borrower
    7. checkin.py: Check in books
    8. checkout.py: Check out books
    9. fines.py: Update and pay fines
    10. search.py: Search for books

How to Run (in Terminal):
    
    1. Be sure you are in the correct directory
        - Command: cd path/to/Database_Project_Boron
    2. Install the required libraries
        - Command: pip install -r requirements.txt
    3. The normalized data is already included in the library_data folder. Running normalize.py will write over the files with the same data.
        - Command: python normalize.py
    2. In connect_db.py and create_library.py, edit 'password' to your actual MySQL root password.
    3. Create and load the database first.
        - Command: python create_library.py
        - Running create_library.py again will reset the database to its original state (with initial data).
    4. Run main.py to access all library system options.
        - Command: python main.py