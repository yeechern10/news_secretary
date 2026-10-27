from datetime import datetime
import json
import openai
import sqlite3

from .system_prompt import event_detector, uncertain_reanalysis_detector
from ..db.retrieve import retrieve_articles_from_db
from ..db.insert_data import insert_events_record, update_event_record
from ..configuration import EVENT_DETECTOR_BASE_URL, EVENT_DETECTOR_MODEL, SQLITE_DB_PATH, UNCERTAIN_ARTICLE_REANALYSIS_CONTENT_TRUNCATE



def detect_event(news_list, api_key = " ", logger=None):
    system_prompt = event_detector[list(event_detector.keys())[-1]]  # Get the last version of the system prompt
    llm_client = openai.OpenAI(api_key=api_key, base_url=EVENT_DETECTOR_BASE_URL)
    
    articles_list = []
    for news in news_list:
        articles_list.append({
            "article_id": news.get("id"),
            "title": news.get("title"),
            "body": news.get("content"),
            "source_name": news.get("source"),
            "published_at": news.get("published_at")
        })
    
    try:
        response = llm_client.chat.completions.create(
            model=EVENT_DETECTOR_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(articles_list)}
            ],
            response_format={"type": "json_object"},
        )
    except openai.error.OpenAIError as e:
        if logger:
            logger.error(f"Error during event extraction: {e}")
        else:
            print(f"Error during event extraction: {e}")
        return None

    return response.choices[0].message.content

def get_published_at_range(articles, ids, current_start=None, current_end=None):
    for id in ids:
        article = articles.get(id)
        if article:
            published_at = article.get("published_at")
            if published_at:
                if current_start is None or published_at < current_start:
                    current_start = published_at
                if current_end is None or published_at > current_end:
                    current_end = published_at
    return current_start, current_end

def event_restructuring(response, news_list, logger=None):
    event_list = []
    filtered_articles = []
    uncertain_articles = []
    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"Error during event restructuring: {e}")
        else:
            print(f"Error during event restructuring: {e}")
        return None    

    data = data.get("events")
    if not data:
        if logger:
            logger.warning("No events found in the response.")
        else:
            print("No events found in the response.")
        return event_list, filtered_articles, uncertain_articles
    
    events = data.get("events")
    for event in data:
        try:
            event_title = event["event_title"]
            article_ids = event["article_ids"]
            confidence = event["confidence_score"]
        except KeyError as e:
            if logger:
                logger.error(f"Error occurred while extracting event data: {e}. Event data: {event}")
            else:
                print(f"Skipping event due to missing title or articles: {event}")
            continue
        
        # Get the published_at range for the articles in this event
        published_at_range_start, published_at_range_end = get_published_at_range(news_list, article_ids)
        
        
        # Append the event to the event_list
        event_list.append({
            "event_title": event_title,
            "article_ids": article_ids,
            "published_at_range_start": published_at_range_start,
            "published_at_range_end": published_at_range_end,
            "confidence_score": confidence
        })
    
    filtered = data.get("filtered_articles", [])
    for article in filtered:
        # Append the articles to the filtered_articles list
        article_id = article.get("article_id") if article.get("article_id") else article.get("id")
        reason = article.get("reason")
        if not article_id or not reason:
            if logger:
                logger.warning(f"Skipping filtered article due to missing article_id or reason: {article}")
            else:
                print(f"Skipping filtered article due to missing article_id or reason: {article}")
            continue
        filtered_articles.append({
            "article_id": article_id,
            "reason": reason
        })
    
    uncertain = data.get("uncertain_articles", [])
    for article in uncertain:
        # Append the articles to the uncertain_articles list
        article_id = article.get("article_id") if article.get("article_id") else article.get("id")
        reason = article.get("reason")
        if not article_id or not reason:
            if logger:
                logger.warning(f"Skipping uncertain article due to missing article_id or reason: {article}")
            else:
                print(f"Skipping uncertain article due to missing article_id or reason: {article}")
            continue
        uncertain_articles.append({
            "article_id": article_id,
            "reason": reason
        })
    
    return event_list, filtered_articles, uncertain_articles

def uncertain_reanalysis(event_dict, filtered_articles, uncertain_articles, articles_dict, content_truncate = UNCERTAIN_ARTICLE_REANALYSIS_CONTENT_TRUNCATE,api_key = " ", logger=None):
    # Get the content of the uncertain articles
    uncertain_article_ids = [article.get("article_id") for article in uncertain_articles]
    
    input_content = {
        "existing_events": [],
        "uncertain_articles": []
    }
    
    for event in event_dict.values():
        published_at_range = f"{event.get('published_at_range_start').strftime('%Y-%m-%d %H:%M:%S')} - {event.get('published_at_range_end').strftime('%Y-%m-%d %H:%M:%S')}" if event.get('published_at_range_start') and event.get('published_at_range_end') else None
        
        input_content["existing_events"].append({
            "event_id": event.get("event_id"),
            "event_title": event.get("event_title"),
            "published_at_range": published_at_range,
            "confidence_score": event.get("confidence_score"),
            "article_titles": [articles_dict.get(article_id).get("title") for article_id in event.get("article_ids") if articles_dict.get(article_id)]
        })
    
    for uncertain_article in uncertain_articles:
        article_id = uncertain_article.get("article_id")
        article = articles_dict.get(article_id)
        if article:
            input_content["uncertain_articles"].append({
                "article_id": article_id,
                "title": article.get("title"),
                "content": article.get("content")[:content_truncate] if article.get("content") else None,  # Limit content to first 2000 characters
                "source_name": article.get("source"),
                "published_at": article.get("published_at"),
            })
    
    llm_client = openai.OpenAI(api_key=api_key, base_url=EVENT_DETECTOR_BASE_URL)
    system_prompt = uncertain_reanalysis_detector[list(uncertain_reanalysis_detector.keys())[-1]]  # Get the last version of the system prompt
    response = llm_client.chat.completions.create(
        model=EVENT_DETECTOR_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(input_content)}
        ],
        response_format={"type": "json_object"},
    )
    
    result = json.loads(response.choices[0].message.content)
    
    if "existing_event_updates" not in result or "new_events" not in result or "filtered_articles" not in result:
        if logger:
            logger.error(f"Unexpected response format from uncertain reanalysis: {result}")
        else:
            print(f"Unexpected response format from uncertain reanalysis: {result}")
        return None, None
    
    for event_update in result["existing_event_updates"]:
        event_id = event_update.get("event_id")
        event_dict[event_id]["article_ids"].extend(event_update.get("new_article_ids", []))
        event_dict[event_id]["confidence_score"] = event_update.get("updated_confidence")
    
    
    
    
    
    
    
def event_detection_pipeline(news_list, api_key = " ", logger=None):
    response = detect_event(news_list, api_key=api_key, logger=logger)
    if response is None:
        return None, None, None
    event_list, filtered_articles, uncertain_articles = event_restructuring(response, news_list, logger=logger)
    
    # save detected events to the database
    with connect_to_postgres() as conn:
        with conn:
            cursor = conn.cursor(row_factory=dict_row)
            for event in event_list:
                insert_events_record(event, cursor, logger=logger)

    