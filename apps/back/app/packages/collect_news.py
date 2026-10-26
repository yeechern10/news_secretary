import cloudscraper
from envs.da.Lib import sqlite3
import requests
import datetime
import trafilatura
from bs4 import BeautifulSoup
import pandas as pd

from ..configuration import NEWS_SOURCE, SQLITE_DB_PATH
from ..packages.logger import get_logger
from ..db.retrieve import get_articles_id
from ..db.insert_data import insert_articles_record

def request_news(query, time_range, serper_api_key, news_list,language ='en', region = None,logger = None):
    # get news
    response = requests.post(
        NEWS_SOURCE,
        headers={
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
            },
        json={
            "q": query,
            "gl": region,
            "hl": language,
            "tbs": time_range
        }
    )

    if response.status_code == 200:
        search_results = response.json()
        news_list.extend(search_results.get('news', []))
        
        return news_list
    else:
        if logger:
            logger.error(f"Search request failed, status code : {response.status_code}, message: {response.text}, query: {query}, time_range: {time_range}, language: {language}, region: {region}")
        else:
            print(f"Search request failed with status code {response.status_code}, message: {response.text}, query: {query}, time_range: {time_range}, language: {language}, region: {region}")
    

def convert_news_date(news_list):
    # Convert relative dates to absolute dates in the news list
    current_date = datetime.datetime.now().date()
    
    for i in range(len(news_list)):
        delta_t = news_list[i].get('date', None)
        if delta_t.endswith('ago'):
            if 'hour' in delta_t:
                hours = int(delta_t.split()[0])
                news_list[i]['date'] = (current_date - datetime.timedelta(hours=hours))
            elif 'day' in delta_t:
                days = int(delta_t.split()[0])
                news_list[i]['date'] = (current_date - datetime.timedelta(days=days))
            elif 'week' in delta_t:
                weeks = int(delta_t.split()[0])
                news_list[i]['date'] = (current_date - datetime.timedelta(weeks=weeks))
            elif 'month' in delta_t:
                months = int(delta_t.split()[0])
                news_list[i]['date'] = (current_date - datetime.timedelta(days=30*months))
            elif 'year' in delta_t:
                years = int(delta_t.split()[0])
                news_list[i]['date'] = (current_date - datetime.timedelta(days=365*years))
            else:
                news_list[i]['date'] = 'null'
        else:
            news_list[i]['date'] = 'null'
    
    return news_list

def add_news_info(news_list, language, region):
    for news in news_list:
        news['language'] = language
        news['region'] = region 
    return news_list
    
def restructure_news_list(news_list):
    restructured_news_list = []
    for news in news_list:
        restructured_news_list.append({
            'title': news['title'],
            'link': news['link'],
            'snippet': news.get('snippet', ''),
            'published_at': news.get('date', None),
            'source': news.get('source', None),
            'language': news.get('language', None),
            'region': news.get('region', None),
            'content': None  # Placeholder for the full article content, to be filled later
        })
    return restructured_news_list

def collect_news(query, time_range, serper_api_key, language='en', region=None, logger=None):
    tbs = 'qdr:d' # default to last 24 hours
    
    current_date = datetime.datetime.now().date()
    
    if time_range == '1d':
        tbs = 'qdr:d'
    elif time_range == '3d':
        tbs = f'cdr:1,cd_min:{(current_date - datetime.timedelta(days=3)).strftime("%m/%d/%Y")},cd_max:{current_date.strftime("%m/%d/%Y")}'
    elif time_range == '1w':
        tbs = 'qdr:w'
    elif time_range == '1m':
        tbs = 'qdr:m'
    elif time_range == '1y':
        tbs = 'qdr:y'
    else:
        if logger:
            logger.warning(f"Invalid time_range '{time_range}' provided. Defaulting to last 24 hours.")
        else:
            print(f"Invalid time_range '{time_range}' provided. Defaulting to last 24 hours.")
    
    news_list = []
    request_news(query, tbs, serper_api_key, news_list, language, region, logger)
    
    # Add language, region, and location information to each news item
    add_news_info(news_list, language, region)
    
    return news_list

def fetch_article_content(url, scraper, logger=None):
    try:
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
        
        # Extract the main content of the article
        # soup = BeautifulSoup(response.content, 'html.parser')

        # container = soup.find('article') or soup.find('main') or soup
        # paragraphs = container.find_all('p')
        # if not paragraphs  and container is not soup:
        #     paragraphs = soup.find_all('p')
        # texts = [p.get_text(strip=True) for p in paragraphs]
        # texts = [t for t in texts if len(t) > 40]
        # article_content = ' '.join(texts).strip()
        text = trafilatura.extract(response.text, include_comments=False, include_tables=False)
        
        # check if the content is empty and log a warning if it is
        if not text or len(text.strip()) == 0:
            if logger:
                logger.warning(f"Empty content extracted from {url}")
            else:
                print(f"Warning: Empty content extracted from {url}")
            return None
        
        return text
    except requests.HTTPError as e:
        # 403/404 errors are common when scraping, so we can log them as warnings instead of errors
        if logger:
            status = e.response.status_code if e.response is not None else "?"
            logger.warning(f"HTTP {status} for {url}")
        return f"fail: {e}"
    except Exception as e:
        if logger:
            logger.error(f"Error fetching article content from {url}: {e}")
        else:
            print(f"Error fetching article content from {url}: {e}")
        return f"fail: {e}"
    
def remove_duplicates(news_list):    
    df = pd.DataFrame(news_list)
    
    # remove duplicates based on url
    df = df.drop_duplicates(subset='link')
    
    # convert back to news_list
    news_list = df.to_dict(orient='records')
    
    return news_list
    
def news_article_pipeline(query_list, time_range, serper_api_key, language='en', region=None):
    logger = get_logger()
    
    news_list = []
    for query in query_list:
        news_list.extend(collect_news(query, time_range, serper_api_key, language, region, logger))
    
    # remove duplicates based on url
    news_list = remove_duplicates(news_list)
    
    # convert relative dates to absolute dates in the news list
    news_list = convert_news_date(news_list)
    
    # restructure the news list
    news_list = restructure_news_list(news_list)
    
    # fetch the full article content for each news item
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )    
    for news in news_list:
        if news.get('link'):
            article_content = fetch_article_content(news['link'], scraper, logger)
            news['content'] = article_content
        else:
            news['content'] = "failed"
    
    # insert articles into the database
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        with conn:
            for article in news_list:
                cursor = conn.cursor()
                insert_articles_record(article, cursor, logger)
    
    article_ids_dict = get_articles_id(news_list)
    
    return article_ids_dict