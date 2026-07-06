import sqlite3

def get_db_connection():

    connection = sqlite3.connect("project_pulse.db") #连接数据库文件，SQLite会自动创建
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            meeting_text TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()

    
