import os
import mysql.connector as sqltor
import schedule
import time

try:
    # Connect to MySQL
    mycon = sqltor.connect(host="localhost", user="root", passwd="1234")
    mycursor = mycon.cursor()

    # Create database if it doesn't exist
    mycursor.execute("CREATE DATABASE IF NOT EXISTS Automatic_Pc_File_Sorter")
    mycon.close()

    # Connect to the created database
    con = sqltor.connect(host="localhost", user="root", passwd="1234", database="Automatic_Pc_File_Sorter")
    cursor = con.cursor()

    # Drop and create Sorter table
    cursor.execute("DROP TABLE IF EXISTS Sorter")
    cursor.execute("CREATE TABLE IF NOT EXISTS Sorter (Name CHAR(200), Type VARCHAR(20), Extensions VARCHAR(10))")

except sqltor.Error as e:
    print(f"Error connecting to MySQL: {e}")
    exit(1)

# Function to create directory if it doesn't exist
def createIfNotExists(folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            print(f"Folder '{folder}' already exists.")
    except OSError as e:
        print(f"Error creating directory {folder}: {e}")

# Function to move files to specified folder without overwriting existing files
def move(folderName, files):
    try:
        destination_folder = folderName
        for file in files:
            source_path = file
            destination_path = os.path.join(destination_folder, os.path.basename(file))

            # Check if source is a directory
            if os.path.isdir(source_path):
                print(f"Skipping directory '{source_path}'")
                continue
            
            # Check if destination folder exists and is empty
            if not os.path.exists(destination_path):
                os.replace(source_path, destination_path)
            else:
                print(f"File '{file}' already exists in '{folderName}'. Skipping move.")

    except FileNotFoundError as e:
        print(f"Error moving files to {folderName}: {e}")

# Function to sort files into directories and populate database
def sort_files():
    try:
        files = os.listdir()
        files.remove('main.py')  # Assuming 'main.py' should not be processed

        createIfNotExists('Images')
        createIfNotExists('Docs')
        createIfNotExists('Medias')
        createIfNotExists('Others')

        categories = {
            'Images': ['.png', '.jpg', '.jpeg', '.jfif', '.tiff', '.gif', '.bmp', '.eps'],
            'Docs': ['.pdf', '.docx', '.doc', '.xlsx', '.accdb', '.pptx', '.txt', '.html'],
            'Medias': ['.mp3', '.mp4', '.mkv', '.avi', '.webm', '.m4v', '.m4a']
        }

        for category, exts in categories.items():
            category_files = []
            for file in files[:]:  # Copy of files list to avoid modification during iteration
                ext = os.path.splitext(file)[1].lower()
                if ext in exts:
                    category_files.append(file)
                    name = os.path.splitext(file)[0].lower()
                    cursor.execute("INSERT INTO Sorter (Name, Type, Extensions) VALUES (%s, %s, %s)", (name, category[:-1], ext))
            
            move(category, category_files)
            files = [file for file in files if file not in category_files]

        # Move remaining files to 'Others' directory
        move('Others', files)
        for file in files:
            name = os.path.splitext(file)[0].lower()
            ext = os.path.splitext(file)[1].lower()
            cursor.execute("INSERT INTO Sorter (Name, Type, Extensions) VALUES (%s, %s, %s)", (name, 'Others', ext))

        con.commit()

    except sqltor.Error as e:
        print(f"Error executing SQL command: {e}")
    except OSError as e:
        print(f"OS Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Initial sorting to ensure database is populated on first run
sort_files()

# User interaction menu
print('*************************Menu****************************')
print()
print("1 - Display all records")
print("2 - Display records of Images Directory")
print("3 - Display records of Document Directory")
print("4 - Display records of Medias Directory")
print("5 - Display records of Others Directory")
print("6 - Schedule file sorting")
print("7 - Exit")

while True:
    choice = input("Enter Your Choice: ")

    try:
        if choice == '1':
            cursor.execute("SELECT * FROM Sorter")
        elif choice == '2':
            cursor.execute("SELECT * FROM Sorter WHERE Type='Image'")
        elif choice == '3':
            cursor.execute("SELECT * FROM Sorter WHERE Type='Document'")
        elif choice == '4':
            cursor.execute("SELECT * FROM Sorter WHERE Type='Media'")
        elif choice == '5':
            cursor.execute("SELECT * FROM Sorter WHERE Type='Others'")
        elif choice == '6':
            print("Choose scheduling basis:")
            print("1. Daily")
            print("2. Weekly")
            print("3. Monthly")
            print("4. Yearly")

            basis_choice = input("Enter your choice (1-4): ")

            if basis_choice == '1':
                schedule.every().day.at("00:00").do(sort_files)
            elif basis_choice == '2':
                schedule.every().monday.at("00:00").do(sort_files)
            elif basis_choice == '3':
                schedule.every().month.at("00:00").do(sort_files)
            elif basis_choice == '4':
                schedule.every().year.at("00:00").do(sort_files)
            else:
                print("Invalid choice. Defaulting to daily.")
                schedule.every().day.at("00:00").do(sort_files)

            print("Sorting scheduled. Press '7' to exit menu and start scheduling.")
            continue
        elif choice == '7':
            con.close()
            print("Exiting...")
            break
        else:
            print("Invalid choice")
            continue

        data = cursor.fetchall()
        count = cursor.rowcount
        print(f"Total number of rows retrieved in the result set: {count}")
        print()

        for row in data:
            print(row)

    except sqltor.Error as e:
        print(f"Error executing SQL command: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

print()
print("These records are stored in the MySQL database 'Automatic_Pc_File_Sorter'")
