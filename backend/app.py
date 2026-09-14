from flask import Flask
from database import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    connection = get_db_connection()

    if connection.is_connected():
        message = "FinalTake backend and MySQL are connected!"
    else:
        message = "Database connection failed."

    connection.close()

    return message


if __name__ == "__main__":
    app.run(debug=True)