import psycopg
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.configuration import SQLITE_DB_PATH, TABLE_NAMES

def structure_keywords(keywords):
    keyword_dict = {}
    for keyword in keywords:
        # ('medtop:20000893', 'artistic cycling', 'Individual or teams on one or two bicycles in an arena. Points are awarded by a jury.', 'arena cycling , bicycle competition , team cycling', 'medtop:20000892', None, '2026-10-16 06:40:33')
        keyword_id, name, description, synonyms, parent_id, child_ids, created_at = keyword
        keyword_dict[keyword_id] = {
            "id": keyword_id,
            "keyword": name,
            "description": description,
            "synonyms": synonyms.split(" , ") if synonyms else [],
            "parent_id": parent_id,
            "child_ids": child_ids.split(" , ") if child_ids else [],
            "created_at": created_at
        }
    return keyword_dict

def retrieve_leaves_keywords_from_db():
    with psycopg.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAMES['keywords']} WHERE child_ids IS NULL")
        keywords = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        keyword_dicts = []
        for row in keywords:
            keyword_dict = {}
            for i in range(len(cursor.description)):
                keyword_dicts.append(dict(zip(columns, row)))
        
    return keyword_dicts



def get_articles_id(news_list):
    articles_dict = {}
    
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        with conn:
            cursor = conn.cursor()
            for news in news_list:
                if news.get('link'):
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT id FROM {TABLE_NAMES['articles']} WHERE link = ?", (news['link'],))
                    result = cursor.fetchone()
                if result:
                    articles_id = result[0]
                    news['id'] = articles_id
                    articles_dict[articles_id] = news
    return articles_dict

def fetch_articles_records(results, articles_dict):
    for row in results:
                articles_dict[row[0]] = {
                    "id": row[0],
                    "created_at": datetime.fromtimestamp(row[1]) if row[1] is not None else None,
                    "title": row[2],
                    "link": row[3],
                    "snippet": row[4],
                    "published_at": datetime.fromtimestamp(row[5]) if row[5] is not None else None,
                    "source": row[6],
                    "language": row[7],
                    "region": row[8],
                    "content": row[9]
                }
    return articles_dict

def retrieve_articles_from_db(cursor, ids: list = None, links: list = None, titles: list = None):
    articles_dict = {}
    if ids:
        placeholders = ', '.join(ids)
        query = f"SELECT id, created_at, title, link, snippet, published_at, source, language, region, content FROM {TABLE_NAMES['articles']} WHERE id IN ({placeholders})"
        cursor.execute(query, ids)
        results = cursor.fetchall()
        articles_dict = fetch_articles_records(results, articles_dict)
        
    if links:
        placeholders = ', '.join(['?'] * len(links))
        query = f"SELECT id, created_at, title, link, snippet, published_at, source, language, region, content FROM {TABLE_NAMES['articles']} WHERE link IN ({placeholders})"
        cursor.execute(query, links)
        results = cursor.fetchall()
        articles_dict = fetch_articles_records(results, articles_dict)
        
    if titles:
        placeholders = ', '.join(['?'] * len(titles))
        query = f"SELECT id, created_at, title, link, snippet, published_at, source, language, region, content FROM {TABLE_NAMES['articles']} WHERE title IN ({placeholders})"
        cursor.execute(query, titles)
        results = cursor.fetchall()
        articles_dict = fetch_articles_records(results, articles_dict)
    
    return articles_dict