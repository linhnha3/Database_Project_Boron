USE DATABASE LIBRARY_BORON;

DROP TABLE IF EXISTS FULL_BOOK;

CREATE TABLE FULL_BOOK AS 
SELECT DISTINCT b.Isbn, b.Title, 
(SELECT GROUP_CONCAT(DISTINCT a.Name ORDER BY a.Name SEPARATOR ', ')
             FROM BOOK_AUTHORS ba
             JOIN AUTHORS a ON ba.Author_id = a.Author_id
             WHERE ba.Isbn = b.Isbn) AS Authors
FROM BOOK b JOIN BOOK_AUTHORS ba ON b.Isbn = ba.Isbn;

ALTER TABLE FULL_BOOK ADD FULLTEXT full_book_index(Isbn, Title, Authors);