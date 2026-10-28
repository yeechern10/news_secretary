import sqlite3
import json
from datetime import datetime
from psycopg import Cursor
from psycopg import errors
from psycopg.rows import dict_row
import re
import uuid
from typing import Literal
from pydantic import validate_call
from logging import Logger

from ..pydantic_model import KeywordModel, ArticleModel, EventModel
from ..db.connect_db import connect_to_postgres
from ..db.retrieve import structure_article
from ..configuration import SQLITE_DB_PATH, TABLE_NAMES

def get_conflict_condition(error_message: str):
    match = re.search(r'Key \((.*?)\)=\((.*?)\)', error_message)
    if match:
        conflict_fields = match.group(1).split(',')
        conflict_values = match.group(2).split(',')
        conditions = []
        for field, value in zip(conflict_fields, conflict_values):
            conditions.append(f"{field.strip()} = '{value.strip()}'")
        conflict_condition = " AND ".join(conditions)
        
        return conflict_condition
    return None

@validate_call
def insert_keywords_record(
    cursor: Cursor,
    keyword_label: str, 
    keyword_type: Literal["iptc_media_topic", "location", "custom"] | None = None,
    keyword_source_id: str = None, 
    keyword_definition: str = None, 
    keyword_synonyms: list = None, 
    keyword_embedding: list[float] = None, 
    logger: Logger = None
    ):
    returning_fields = ", ".join(["id", "source_id", "label", "definition", "synonyms", "type", "embedding", "created_at", "last_updated"])
    
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['keywords']} 
            (source_id, label, definition, synonyms, keyword_type, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING {returning_fields}
        """, (
            keyword_source_id,
            keyword_label,
            keyword_definition,
            keyword_synonyms,
            keyword_type,
            keyword_embedding
        ))
        result = cursor.fetchone()
        if result:
            result['embedded'] = True if result.pop('embedding') is not None else False
            return KeywordModel(**result)
    except errors.UniqueViolation as e:
        if logger:
            logger.error(f"Error inserting keyword {keyword_source_id} {keyword_label}: {e.diag.message_detail}")

        conflict_condition = get_conflict_condition(e.diag.message_detail)
        
        # retrieve the existing record
        if conflict_condition:                
            with connect_to_postgres() as new_conn:
                with new_conn:
                    new_cursor = new_conn.cursor(row_factory=dict_row)
                    new_cursor.execute(f"""
                        SELECT {returning_fields} FROM {TABLE_NAMES['keywords']} WHERE {conflict_condition}
                    """)
                    existing_record = new_cursor.fetchone()
                    existing_record['embedded'] = True if existing_record.pop('embedding') is not None else False
                    if logger:
                        logger.info(f"Existing record: {existing_record}")
                    
                    return KeywordModel(**existing_record)
        return None
    except errors.IntegrityError as e:
        if logger:
            logger.error(f"Integrity error inserting keyword {keyword_source_id} {keyword_label}: {e.diag.message_detail}")
        return None
            


def insert_articles_record(
    cursor: Cursor,
    article_title: str,
    article_link: str,
    article_snippet: str = None,
    article_published_at: datetime = None,
    article_source: str = None,
    article_language: str = None,
    article_content: str = None,
    article_content_status: Literal["pending", "completed", "failed"] = None,
    article_content_error: str = None,
    article_embedding: list[float] = None,
    logger: Logger = None
    ):
    returning_fields = ", ".join([
        "id", "title", "link", "snippet", "published_at", 
        "source", "language", "content", "content_status",
        "content_error", "embedding", "created_at", "last_updated"
    ])

    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['articles']} 
            (title, link, snippet, published_at, source, language, 
            content, content_status, content_error, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {returning_fields}
        """, (
            article_title,
            article_link,
            article_snippet,
            article_published_at.timestamp() if article_published_at else None,
            article_source,
            article_language,
            article_content,
            article_content_status,
            article_content_error,
            article_embedding
        ))
        returned_article = cursor.fetchone()
        if returned_article:
            returned_article['embedded'] = True if returned_article.pop('embedding') is not None else False
            return ArticleModel(**returned_article)
        return None
    except errors.UniqueViolation as e:
        if logger:
            logger.error(f"Error inserting article {article_title}: {e.diag.message_detail}")

        conflict_condition = get_conflict_condition(e.diag.message_detail)
                
        # retrieve the existing record
        if conflict_condition:                
            with connect_to_postgres() as new_conn:
                with new_conn:
                    new_cursor = new_conn.cursor(row_factory=dict_row)
                    new_cursor.execute(f"""
                        SELECT {returning_fields} 
                        FROM {TABLE_NAMES['articles']} 
                        WHERE {conflict_condition}
                    """)
                    existing_record = new_cursor.fetchone()
                    if logger:
                        logger.info(f"Existing record: {existing_record}")
                    if existing_record:
                        existing_record['embedded'] = True if existing_record.pop('embedding') is not None else False
                        return ArticleModel(**existing_record)
        return None
    except errors.IntegrityError as e:
        if logger:
            logger.error(f"Integrity error inserting article {article_title}: {e.diag.message_detail}")
        return None

def insert_events_record(
    cursor: Cursor, 
    event_title: str,
    event_summary: str = None,
    event_published_at_range_start: datetime = None,
    event_published_at_range_end: datetime = None,
    event_confidence_score: float = None,
    event_importance_score: int = None,
    event_embedding: list[float] = None,
    logger=None
    ):
    returning_fields = ", ".join([
        "id", "title", "summary", "published_at_range_start",
        "published_at_range_end", "confidence_score", "importance_score",
        "embedding", "created_at", "last_updated"
    ])
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAMES['events']} 
            (title, summary, published_at_range_start, 
            published_at_range_end, confidence_score,
            importance_score, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING {returning_fields}
        """, (
            event_title,
            event_summary,
            event_published_at_range_start,
            event_published_at_range_end,
            event_confidence_score,
            event_importance_score,
            event_embedding
        ))
        
        returned_event = cursor.fetchone()
        returned_event['embedded'] = True if returned_event.pop('embedding') is not None else False
        
        return EventModel(**returned_event)
    except errors.UniqueViolation as e:
        if logger:
            logger.error(f"Error inserting event {event_title}: {e.diag.message_detail}")
            
        conflict_condition = get_conflict_condition(e.diag.message_detail)
                        
        # retrieve the existing record
        if conflict_condition:  
            with connect_to_postgres() as new_conn:
                with new_conn:
                    new_cursor = new_conn.cursor(row_factory=dict_row)
                    new_cursor.execute(f"""
                        SELECT {returning_fields}
                        FROM {TABLE_NAMES['events']} 
                        WHERE {conflict_condition}
                    """)
                    existing_record = new_cursor.fetchone()
                    if logger:
                        logger.info(f"Existing record: {existing_record}")
                    if existing_record:
                        existing_record['embedded'] = True if existing_record.pop('embedding') is not None else False
                        return EventModel(**existing_record)
                    
        return None

def update_event_articles(event: dict, cursor, logger=None):
    try:
        cursor.execute(f"""
            UPDATE {TABLE_NAMES['events']}
            SET article_ids = %s, published_at_range_start = %s, published_at_range_end = %s, confidence_score = %s
            WHERE event_id = %s
        """, (
            json.dumps(event['article_ids']),
            event.get('published_at_range_start', None).totimestamp() if event.get('published_at_range_start', None) else None,
            event.get('published_at_range_end', None).totimestamp() if event.get('published_at_range_end', None) else None,
            event.get('confidence_score', None),
            event['event_id']
        ))
    except errors.UniqueViolation as e:
        if logger:
            logger.error(f"Error updating event {event['event_title']}: {e}")
        else:
            print(f"Error updating event {event['event_title']}: {e}")