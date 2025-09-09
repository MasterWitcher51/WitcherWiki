from bestiary import load_monsters, Monster

monsters = load_monsters()


def list_all_monsters():
    # Function that list all monster names
    print("=== Monster List ==========")
    for m in monsters:
        print(m.Name)
    print("===========================")

def show_details():
    # Function that show details of monster by name
    choice = input("Enter a monster for its details: ")
    print("=== Monster Info ==========")
    for m in monsters:
        if choice == m.Name:
            print(m)
    print("===========================")

           
def search_by_class():
    # Function that searches for mosnters in a certain class
    choice = input("Enter a class to see associated monsters: ")
    for m in monsters:
        if choice == m.Class:
            print(m.Name)

def search_by_loot():
    # Function that list monsters with a certain drop
    choice = input("Enter a loot drop to see monster who drops it: ")
    for m in monsters:
        if choice.lower() in [item.lower() for item in m.Loot]:
            print(m.Name)


def main_menu():
    print("Welcome to the Witcher 3 Bestiary App, select an option from below")
    print("1. List all monsters")
    print("2. Show details of monster")
    print("3. Search by class")
    print("4. Search by loot")
    print("5. Exit")

    while True:
        choice = input("Select an option from 1-5: ")

        if choice == "1":
            list_all_monsters()
        elif choice == "2":
            show_details()
        elif choice == "3":
            search_by_class()
        elif choice == "4":
            search_by_loot()
        elif choice == "5":
            print("End of program, Goodbye!!")
            break
        else:
            print("Wrong choice try again")

if __name__ == "__main__":
    main_menu()


