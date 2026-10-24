import json
import openai
import sqlite3

from .system_prompt import event_detector
from ..db.retrieve import retrieve_articles_from_db
from ..configuration import EVENT_DETECTOR_BASE_URL, EVENT_DETECTOR_MODEL, SQLITE_DB_PATH



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
            "published_at": news.get("date")
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

def event_restructuring(response, logger=None):
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
        event_title = event.get("event_title")
        articles = event.get("article_ids")
        published_at_range = event.get("published_at_range")
        confidence = event.get("confidence")
        if not event_title or not articles:
            if logger:
                logger.warning(f"Skipping event due to missing title or articles: {event}")
            else:
                print(f"Skipping event due to missing title or articles: {event}")
            continue
        
        # Append the event to the event_list
        event_list.append({
            "event_title": event_title,
            "articles": articles,
            "published_at_range": published_at_range,
            "confidence": confidence
        })
    
    filtered = data.get("filtered_articles", [])
    for article in filtered:
        # Append the articles to the filtered_articles list
        article_id = article.get("article_id")
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
        article_id = article.get("article_id")
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

def uncertain_reanalysis(event_list, filtered_articles, uncertain_articles, api_key = " ", logger=None):
    # Get the content of the uncertain articles
    uncertain_article_ids = [article.get("article_id") for article in uncertain_articles]
    
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        with conn:
            cursor = conn.cursor()
            articles = retrieve_articles_from_db(cursor, ids=uncertain_article_ids)
    
    
    
    
def event_detection_pipeline(news_list, api_key = " ", logger=None):
    response = detect_event(news_list, api_key=api_key, logger=logger)
    if response is None:
        return None, None, None
    event_list, filtered_articles, uncertain_articles = event_restructuring(response, logger=logger)
    return event_list, filtered_articles, uncertain_articles