import pandas as pd

from ..packages.collect_news import news_article_pipeline
from ..packages.logger import get_logger
from ..llm.summarize_article import summarize_articles
from ..llm.detect_event import detect_evention_pipeline, event_detection_pipeline
from ..configuration import  ARTICLE_SUMMARIZER_BASE_URL

def articles_request_event_pipeline(query_list, time_range, serper_api_key, article_summarizer_api_key, keywords_list, language='en', region=None, logger=None):
    if logger is None:
        logger = get_logger()
    
    news_list = news_article_pipeline(query_list, time_range, serper_api_key, language, region)
    
    # detect events from the news articles
    event_list, filtered_articles, uncertain_articles = event_detection_pipeline(news_list, api_key=article_summarizer_api_key, logger=logger)
    
    
    return news_list

