from search import search
from checkout import checkout_book
from checkin import checkin_book
from fines import update_fines, pay_fines
from borrower import add_borrower


def main():
    print("📚 Welcome to the Library Management System 📚")

    while True:
        print("""
            Choose an action:
            1. Search Books
            2. Checkout Book
            3. Checkin Book
            4. Pay Fines
            5. Add Borrower
            6. Exit
        """)

        choice = input("Enter choice: ").strip()

        if choice == '1':
            query = input("🔍 Enter search term (ISBN, Title, or Author): ")
            search(query)

        elif choice == '2':
            update_fines()
            isbn = input("Enter ISBN to Check Out: ")
            card_id = input("Enter Borrower's Card ID: ")
            checkout_book(isbn, card_id)

        elif choice == '3':
            print("\nPress Enter to Skip Any Field")
            isbn = input("Enter ISBN to Check In: ")
            card_id = input("Enter Borrower's Card ID: ")
            name = input("Enter Borrower Name: ")
            checkin_book(isbn, card_id, name)

        elif choice == '4':
            update_fines()
            pay_fines()

        elif choice == '5':
            add_borrower()

        elif choice == '6':
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
