import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.configuration import SQLITE_DB_PATH, TABLE_NAMES

def retrieve_leaves_keywords_from_db():
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAMES['keywords']} WHERE parent_id IS NULL")
        keywords = cursor.fetchall()
    return keywords

def structure_keywords(keywords):
    keyword_dict = {}
    for keyword in keywords:
        # ('medtop:20000893', 'artistic cycling', 'Individual or teams on one or two bicycles in an arena. Points are awarded by a jury.', 'arena cycling , bicycle competition , team cycling', 'medtop:20000892', None, '2026-10-16 06:40:33')
        keyword_id, name, description, synonyms, parent_id, child_ids, created_at = keyword
        keyword_dict[keyword_id] = {
            "keyword": name,
            "description": description,
            "synonyms": synonyms.split(" , ") if synonyms else [],
            "parent_id": parent_id,
            "child_ids": child_ids.split(" , ") if child_ids else [],
            "created_at": created_at
        }
    return keyword_dict

def get_articles_id(news_list):
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
    return news_list

def fetch_articles_records(results, articles_set):
    for row in results:
                articles_set.add({
                    "id": row[0],
                    "created_at": row[1],
                    "title": row[2],
                    "link": row[3],
                    "snippet": row[4],
                    "published_at": row[5],
                    "source": row[6],
                    "language": row[7],
                    "region": row[8],
                    "content": row[9]
                })
    return articles_set

def retrieve_articles_from_db(cursor, ids: list = None, links: list = None, titles: list = None):
    articles_set = set()
    if ids:
        placeholders = ', '.join(ids)
        query = f"SELECT id, created_at, title, link, snippet, published_at, source, language, region, content FROM {TABLE_NAMES['articles']} WHERE id IN ({placeholders})"
        cursor.execute(query, ids)
        results = cursor.fetchall()
        articles_set = fetch_articles_records(results, articles_set)
        
    if links:
        placeholders = ', '.join(['?'] * len(links))
        query = f"SELECT id, created_at, title, link, snippet, published_at, source, language, region, content FROM {TABLE_NAMES['articles']} WHERE link IN ({placeholders})"
        cursor.execute(query, links)
        results = cursor.fetchall()
        articles_set = fetch_articles_records(results, articles_set)
        
    if titles:
        placeholders = ', '.join(['?'] * len(titles))
        query = f"SELECT id, created_at, title, link, snippet, published_at, source, language, region, content FROM {TABLE_NAMES['articles']} WHERE title IN ({placeholders})"
        cursor.execute(query, titles)
        results = cursor.fetchall()
        articles_set = fetch_articles_records(results, articles_set)
    
    return list(articles_set)