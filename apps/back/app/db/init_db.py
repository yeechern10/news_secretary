import sqlite3
import json

from ..packages.logger import get_logger
from ..configuration import DB_DIR, SQLITE_DB_PATH, TABLE_NAMES

def definitions_to_schema(definitions):
    schema = {}
    for line in definitions.strip().splitlines():
        line = line.strip()
        if line:
            field_name, constraint = line.split(maxsplit=1)
            schema[field_name] = constraint
    return schema

def create_save_schema(definitions, table_name):
    schema = definitions_to_schema(definitions)
    schema_file_path = DB_DIR / f"{table_name}.json"
    with open(schema_file_path, 'w') as f:
        json.dump(schema, f, indent=4)

def create_users_table(cursor, logger=None):
    definitions = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        country_code TEXT,
        language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["users"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["users"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating users table: {e}")
        else:
            print(f"Error creating users table: {e}")

def create_keywords_table(cursor, logger=None):
    definitions = """
        id TEXT PRIMARY KEY,
        keyword TEXT NOT NULL,
        definition TEXT,
        synonyms TEXT,
        parent_id TEXT,
        child_ids TEXT,
        source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["keywords"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["keywords"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating keywords table: {e}")
        else:
            print(f"Error creating keywords table: {e}")

def create_user_keywords_table(cursor, logger=None):
    definitions = """
        user_id INTEGER NOT NULL UNIQUE,
        keyword_id TEXT NOT NULL UNIQUE,
        interest_level INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["user_keywords"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["user_keywords"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating user_keywords table: {e}")
        else:
            print(f"Error creating user_keywords table: {e}")

def create_articles_table(cursor, logger=None):
    definitions = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        title TEXT NOT NULL,
        link TEXT NOT NULL UNIQUE,
        snippet TEXT,
        published_at TIMESTAMP,
        source TEXT,
        language TEXT,
        region TEXT,
        content TEXT
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["articles"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["articles"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating articles table: {e}")
        else:
            print(f"Error creating articles table: {e}")

def create_evets_table(cursor, logger=None):
    definitions = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_title TEXT NOT NULL,
        event_description TEXT,
        event_summary TEXT,
        tags TEXT,
        summary TEXT,
        importance_score INTEGER,
        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["events"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["events"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating events table: {e}")
        else:
            print(f"Error creating events table: {e}")

def create_user_article_interactions_table(cursor, logger=None):
    definitions = """
        user_id INTEGER NOT NULL,
        article_id INTEGER NOT NULL,
        interaction_type TEXT NOT NULL,
        interaction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["user_article_interactions"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["user_article_interactions"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating user_article_interactions table: {e}")
        else:
            print(f"Error creating user_article_interactions table: {e}")

def create_user_event_interactions_table(cursor, logger=None):
    definitions = """
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        interaction_type TEXT NOT NULL,
        interaction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, event_id)
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["user_event_interactions"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["user_event_interactions"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating user_event_interactions table: {e}")
        else:
            print(f"Error creating user_event_interactions table: {e}")

def create_event_article_relationships_table(cursor, logger=None):
    definitions = """
        event_id INTEGER NOT NULL,
        article_id INTEGER NOT NULL,
        PRIMARY KEY (event_id, article_id)
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["event_article_relationships"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["event_article_relationships"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating event_article_relationships table: {e}")
        else:
            print(f"Error creating event_article_relationships table: {e}")

def create_events_keywords_relationships_table(cursor, logger=None):
    definitions = """
        event_id INTEGER NOT NULL,
        keyword_id TEXT NOT NULL,
        relevance_score INTEGER,
        PRIMARY KEY (event_id, keyword_id)
    """
    try:
        cursor.execute(f'CREATE TABLE {TABLE_NAMES["events_keywords_relationships"]} ( {definitions} )')
        create_save_schema(definitions, TABLE_NAMES["events_keywords_relationships"])
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error creating events_keywords_relationships table: {e}")
        else:
            print(f"Error creating events_keywords_relationships table: {e}")



def init_db():
    logger = get_logger("init_db")
    # Create articles.db if it doesn't exist
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Create users table
        create_users_table(cursor, logger)
        conn.commit()
    

        # Create articles tables
        create_articles_table(cursor, logger)
        conn.commit()
        
        # Create events table
        create_evets_table(cursor, logger)
        conn.commit()
        
        # Create keywords table
        create_keywords_table(cursor, logger)
        conn.commit()
        
        # Create user keywords table
        create_user_keywords_table(cursor, logger)
        conn.commit()
                
        # Create a table to store the relationship between users and articles
        create_user_article_interactions_table(cursor, logger)
        conn.commit()
        
        # Create a table to store the relationship between users and events
        create_user_event_interactions_table(cursor, logger)
        conn.commit()

        # Create a table to store the relationship between events and articles
        create_event_article_relationships_table(cursor, logger)
        conn.commit()
        
        # Create a table to store the relationship between events and keywords
        create_events_keywords_relationships_table(cursor, logger)
        conn.commit()

if __name__ == "__main__":
    init_db()