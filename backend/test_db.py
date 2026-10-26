
from sqlalchemy import text
from database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE(), VERSION()"))
        database_name, version = result.fetchone()

        print("MySQL connection successful!")
        print("Database:", database_name)
        print("MySQL version:", version)

except Exception as error:
    print("MySQL connection failed.")
    print("Error:", error)
