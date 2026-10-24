import sqlite3

from ..configuration import SQLITE_DB_PATH, TABLE_NAMES



def insert_keywords_record(keyword, table_name ,cursor, conn):
    try:
        cursor.execute(f"""
            INSERT INTO {table_name} (id, keyword, definition, synonyms, parent_id, child_ids)
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
        conn.commit()
        conn.close()
        print(f"Error inserting keyword {id} {keyword['label']}: {e}")
        if "UNIQUE constraint failed" in str(e):
            # retrieve the existing record
            conflict_field = str(e).split('.')[-1]
            field_value_map = {
                "id": id,
                "keyword": keyword["label"]
            }
            with sqlite3.connect(SQLITE_DB_PATH) as conn:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        SELECT * FROM {TABLE_NAMES['keywords']} WHERE {conflict_field} = ?
                    """, (field_value_map[conflict_field],))
                    existing_record = cursor.fetchone()
                    print(f"Existing record: {existing_record}")
        return e


def insert_articles_record(article, cursor, conn, logger=None):
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['articles']} (title, link, snippet, published_at, source, language, region, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article['title'],
            article['link'],
            article.get('snippet', None),
            article.get('date', None),
            article.get('source', None),
            article.get('language', None),
            article.get('region', None),
            article.get('content', None)
        ))
    except sqlite3.IntegrityError as e:
        conn.commit()
        conn.close()
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
            with sqlite3.connect(SQLITE_DB_PATH) as conn:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        SELECT * FROM {TABLE_NAMES['articles']} WHERE {conflict_field} = ?
                    """, (field_value_map[conflict_field],))
                    existing_record = cursor.fetchone()
                    if logger:
                        logger.info(f"Existing record: {existing_record}")
                    else:
                        print(f"Existing record: {existing_record}")