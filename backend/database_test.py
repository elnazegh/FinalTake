from database import get_db_connection


connection = get_db_connection()

cursor = connection.cursor()

cursor.execute("SELECT * FROM users")

users = cursor.fetchall()

for user in users:
    print(user)

cursor.close()
connection.close()