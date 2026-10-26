import sqlite3
import json
import datetime

from ..configuration import SQLITE_DB_PATH, TABLE_NAMES



def insert_keywords_record(keyword ,cursor, logger=None):
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['keywords']} (id, keyword, definition, synonyms, parent_id, child_ids)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            id,
            keyword["label"],
            keyword["definition"],
            " , ".join(keyword["synonyms"]) if keyword.get("synonyms") else None,
            keyword["parent"],
            " , ".join(keyword["children"]) if keyword.get("children") else None
        ))
    except sqlite3.IntegrityError as e:
        print(f"Error inserting keyword {id} {keyword['label']}: {e}")
        if "UNIQUE constraint failed" in str(e):
            # retrieve the existing record
            conflict_field = str(e).split('.')[-1]
            field_value_map = {
                "id": id,
                "keyword": keyword["label"]
            }
            with sqlite3.connect(SQLITE_DB_PATH) as new_conn:
                with new_conn:
                    new_cursor = new_conn.cursor()
                    new_cursor.execute(f"""
                        SELECT * FROM {TABLE_NAMES['keywords']} WHERE {conflict_field} = ?
                    """, (field_value_map[conflict_field],))
                    existing_record = new_cursor.fetchone()
                    print(f"Existing record: {existing_record}")
        return e


def insert_articles_record(article, cursor, logger=None):
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['articles']} (title, link, snippet, published_at, source, language, region, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article['title'],
            article['link'],
            article.get('snippet', None),
            article.get('published_at').timestamp() if article.get('published_at', None) else None,
            article.get('source', None),
            article.get('language', None),
            article.get('region', None),
            article.get('content', None)
        ))
    except sqlite3.IntegrityError as e:
        if logger:
            logger.error(f"Error inserting article {article['title']}: {e}")
        else:
            print(f"Error inserting article {article['title']}: {e}")
        if "UNIQUE constraint failed" in str(e):
            # retrieve the existing record
            conflict_field = str(e).split('.')[-1]
            field_value_map = {
                "title": article['title'],
                "link": article['link']
            }
            with sqlite3.connect(SQLITE_DB_PATH) as new_conn:
                with new_conn:
                    new_cursor = new_conn.cursor()
                    new_cursor.execute(f"""
                        SELECT * FROM {TABLE_NAMES['articles']} WHERE {conflict_field} = ?
                    """, (field_value_map[conflict_field],))
                    existing_record = new_cursor.fetchone()
                    if logger:
                        logger.info(f"Existing record: {existing_record}")
                    else:
                        print(f"Existing record: {existing_record}")
                        
def insert_events_record(event: dict, cursor, saved_events: dict, logger=None):
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['events']} (event_title, article_ids, published_at_range_start, published_at_range_end, confidence_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event['event_title'],
            json.dumps(event['article_ids']),
            event.get('published_at_range_start', None).totimestamp() if event.get('published_at_range_start', None) else None,
            event.get('published_at_range_end', None).totimestamp() if event.get('published_at_range_end', None) else None,
            event.get('confidence_score', None)
        ))
    except sqlite3.IntegrityError as e:
        if logger:
            logger.error(f"Error inserting event {event['event_title']}: {e}")
        else:
            print(f"Error inserting event {event['event_title']}: {e}")
        if "UNIQUE constraint failed" in str(e):
            # retrieve the existing record
            conflict_field = str(e).split('.')[-1]
            field_value_map = {
                "event_title": event['event_title']
            }
            with sqlite3.connect(SQLITE_DB_PATH) as new_conn:
                with new_conn:
                    new_cursor = new_conn.cursor()
                    new_cursor.execute(f"""
                        SELECT * FROM {TABLE_NAMES['events']} WHERE {conflict_field} = ?
                    """, (field_value_map[conflict_field],))
                    existing_record = new_cursor.fetchone()
                    if logger:
                        logger.info(f"Existing record: {existing_record}")
                    else:
                        print(f"Existing record: {existing_record}")

def update_event_articles(event: dict, cursor, logger=None):
    try:
        cursor.execute(f"""
            UPDATE {TABLE_NAMES['events']}
            SET article_ids = ?, published_at_range_start = ?, published_at_range_end = ?, confidence_score = ?
            WHERE event_id = ?
        """, (
            json.dumps(event['article_ids']),
            event.get('published_at_range_start', None).totimestamp() if event.get('published_at_range_start', None) else None,
            event.get('published_at_range_end', None).totimestamp() if event.get('published_at_range_end', None) else None,
            event.get('confidence_score', None),
            event['event_id']
        ))
    except sqlite3.Error as e:
        if logger:
            logger.error(f"Error updating event {event['event_title']}: {e}")
        else:
            print(f"Error updating event {event['event_title']}: {e}")