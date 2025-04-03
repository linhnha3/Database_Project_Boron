from connect_db import connect_db
import re

def add_borrower():
    conn = connect_db()
    cursor = conn.cursor()

    #Create new borrower card_id
    def get_new_card_id():
        cursor.execute('SELECT Card_id FROM BORROWER ORDER BY Card_id DESC LIMIT 1')
        last_id = cursor.fetchone()
        num = int(last_id[0][2:])
        num += 1
        new_id = 'ID' + str(num).zfill(6)
        return new_id
        
    #Check for correct SSN format
    ssn = input('\nEnter Borrower SSN in the Format xxx-xx-xxxx: ')
    pattern = r'\d\d\d-\d\d-\d\d\d\d'
    while re.match(pattern, ssn) == None:
        print('\n❌ The entered SSN did not have the correct format.')
        ssn = input('\nEnter Borrower SSN in the Format xxx-xx-xxxx: ')

    #Check if entered SSN is already used by another borrower
    cursor.execute('SELECT COUNT(*) FROM BORROWER WHERE Ssn=%s', (ssn,))
    present = cursor.fetchone()

    if present[0] == 1:
        print('\n❌ The entered SSN is already in use.')
    elif present[0] == 0:
        name = input('\nEnter Borrower Full Name: ')
        address = input('\nEnter Borrower Address: ')

        phone = input('\nEnter Borrower Phone Number in the Format (xxx) xxx-xxxx or Press Enter to Skip: ')
        #Check phone number format
        pattern = r'\(\d\d\d\) \d\d\d-\d\d\d\d|^$'
        while re.match(pattern, phone) == None:
            print('\n❌ The entered phone number did not have the correct format.')
            phone = input('\nEnter Borrower Phone Number in the Format (xxx) xxx-xxxx or Press Enter to Skip: ')
        
        #If no phone number is entered, BORROWER.phone will equal NULL
        if phone == '':
            phone = None
        
        new_id = get_new_card_id()
        cursor.execute('INSERT INTO BORROWER VALUES (%s, %s, %s, %s, %s)', (new_id, ssn, name, address, phone))
        conn.commit()
        conn.close()
        print(f'\n✅ Borrower {new_id} has been successfully added.')
