import sqlite3

class ChatGPTDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        
    def create_table(self, table_name, columns):
        '''
        Creates a new table in the database with the given name and column 
        
        '''
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns}) "
        self.cursor.execute(create_table_sql)
        self.conn.commit()
    
    def insert_record(self, table_name, columns, record):
        '''
        Insert a record to a target table with values separate by a comm
        '''
        sql = f'INSERT INTO {table_name} ({columns}) VALUES ({record})'
        print(sql)
        self.cursor.execute(sql)
        self.conn.commit()
    
    def close(self):
        self.cursor.close()
        self.conn.close()