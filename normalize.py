import pandas as pd

#Read books and borrorwers in as dataframes
books = pd.read_csv('books.csv', sep='\t')
borrowers = pd.read_csv('borrowers.csv')

#Copy ISBN10 and Title from books into book.csv with uppercase convention
book = pd.DataFrame(columns=['Isbn', 'Title'])
book['Isbn'] = books['ISBN10']
book['Title'] = books['Title'].str.upper()

#Create dataframes for book_authors and authors
book_authors = pd.DataFrame(columns=['Author_id', 'Isbn'])
authors = pd.DataFrame(columns=['Author_id', 'Name'])
books['Author'] = books['Author'].fillna('Unknown Author')  
authors.loc[len(authors)] = [0, 'UNKNOWN AUTHOR'] #Default Author_id and Name for unknown authors
next_id = 1   #To create unique author ids

#Split author cells by ',' and strip leading/tailing spaces and change case of each name
for _, row in books.iterrows():
    names = row['Author'].split(",")
    for n in names:
        #Normalize author names to have no spaces between inital letters (X.X. LASTNAME)
        n = n.replace('. ', '.').strip().upper()
        new = '. '
        n = new.join(n.rsplit('.', 1)).replace('  ', ' ')
        #If new author, create id and add to authors and book_authors
        if n not in authors['Name'].values:
            authors.loc[len(authors)] = [next_id, n]
            book_authors.loc[len(book_authors)] = [next_id, row['ISBN10']]
            next_id += 1
        else:
            #Author name and id exists
            #Find id from name and add to book_authors
            id = authors.loc[authors['Name'] == n]['Author_id'].item()
            book_authors.loc[len(book_authors)] = [id, row['ISBN10']]
book_authors = book_authors.drop_duplicates()

#Copy necessary columns from borrowers to borrower
borrower = pd.DataFrame(columns=['Card_id', 'Ssn', 'Bname', 'Address', 'Phone'])
borrower['Card_id'] = borrowers['ID0000id']
borrower['Ssn'] = borrowers['ssn']
#Concatenate first and last names and uppercase
borrower['Bname'] = borrowers['first_name'].str.upper() + ' ' + borrowers['last_name'].str.upper()
borrower['Address'] = borrowers['address']  
borrower['Phone'] = borrowers['phone']

#Export all dataframes to csv files
book.to_csv('book.csv', sep='\t', index=False)
book_authors.to_csv('book_authors.csv', index=False)
authors.to_csv('authors.csv', index=False)
borrower.to_csv('borrower.csv', index=False)