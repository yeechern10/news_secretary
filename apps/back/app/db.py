import sqlite3

from ...comfiguration import sqlite_db_path

def init_db():    
    # Create articles.db if it doesn't exist
    with sqlite3.connect(sqlite_db_path) as conn:
        cursor = conn.cursor()
        
        # Create users table
        fields_list = [
            ['id', 'INTEGER', 'PRIMARY KEY AUTOINCREMENT', "COMMENT 'Unique identifier for each user'"],
            ['username', 'TEXT', 'NOT NULL UNIQUE', "COMMENT 'The username of the user'"],
            ['country_code', 'TEXT', None, "COMMENT 'The country code of the user'"],
            ['location', 'TEXT', None, "COMMENT 'The location of the user'"],
            ['language', 'TEXT', None, "COMMENT 'The preferred language of the user'"],
            ['created_at', 'TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP', "COMMENT 'Timestamp when the user was created'"]
        ]
        field_definitions = ', '.join([f"{field[0]} {field[1]} {field[2]} {field[3]}" for field in fields_list])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS users ( {field_definitions} )')
        conn.commit()

        # Create user keywords table
        fields_list = [
            ['id', 'INTEGER', 'PRIMARY KEY AUTOINCREMENT', "COMMENT 'Unique identifier for each user keyword'"],
            ['user_id', 'INTEGER', 'NOT NULL', "COMMENT 'The ID of the user'"],
            ['keyword', 'TEXT', 'NOT NULL', "COMMENT 'The keyword associated with the user'"],
            ['created_at', 'TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP', "COMMENT 'Timestamp when the user keyword was added'"]
        ]
        field_definitions = ', '.join([f"{field[0]} {field[1]} {field[2]} {field[3]}" for field in fields_list])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS user_keywords ( {field_definitions} )')
        conn.commit()

        # Create articles tables
        fields_list = [
            ['id', 'INTEGER', 'PRIMARY KEY AUTOINCREMENT', "COMMENT 'Unique identifier for each news article'"],
            ['created_at', 'TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP', "COMMENT 'Timestamp when the news article was added to the database'"],
            ['title', 'TEXT', 'NOT NULL', "COMMENT 'The title of the news article'"],
            ['content', 'TEXT', 'NOT NULL', "COMMENT 'The content of the news article'"],
            ['source', 'TEXT', None, "COMMENT 'The source of the news article'"],
            ['url', 'TEXT', None, "COMMENT 'The URL of the news article'"],
            ['language', 'TEXT', None, "COMMENT 'The language of the news article'"],
            ['region', 'TEXT', None, "COMMENT 'The region of the news article'"],
            ['location', 'TEXT', None, "COMMENT 'The location of the news article'"],
            ['published_at', 'TIMESTAMP', None, "COMMENT 'The timestamp when the news article was published'"],
            ['tags', 'TEXT', None, "COMMENT 'The tags associated with the news article'"],
            ['summary', 'TEXT', None, "COMMENT 'A brief summary of the news article'"]
        ]   # ['field_name', 'data_type', 'constraints', 'comment']
        
        field_definitions = ', '.join([f"{field[0]} {field[1]} {field[2]} {field[3]}" for field in fields_list])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS articles ( {field_definitions} )')
        conn.commit()
        
        # Create a table to store the relationship between users and articles
        fields_list = [
            ['user_id', 'INTEGER', 'NOT NULL', "COMMENT 'The ID of the user'"],
            ['article_id', 'INTEGER', 'NOT NULL', "COMMENT 'The ID of the article'"],
            ['interaction_type', 'TEXT', 'NOT NULL', "COMMENT 'The type of interaction (e.g., view, like, share)'"],
            ['interaction_timestamp', 'TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP', "COMMENT 'Timestamp when the interaction occurred'"]
        ]
        field_definitions = ', '.join([f"{field[0]} {field[1]} {field[2]} {field[3]}" for field in fields_list])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS user_article_interactions ( {field_definitions} )')
        conn.commit()
    


