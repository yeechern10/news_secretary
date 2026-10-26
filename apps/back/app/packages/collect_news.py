import cloudscraper
from envs.da.Lib import sqlite3
import requests
import datetime
import trafilatura
import pandas as pd
from psycopg.rows import dict_row

from ..configuration import NEWS_SOURCE, SQLITE_DB_PATH, SERPER_API
from ..packages.logger import get_logger
from ..db.connect_db import connect_to_postgres
from ..db.retrieve import get_articles_id, check_article_exists_embedded
from ..db.insert_data import insert_articles_record

def request_news(query, time_range, news_list,language ='en', region = None,logger = None):
    # get news
    response = requests.post(
        NEWS_SOURCE,
        headers={
            "X-API-KEY": SERPER_API,
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

def collect_news(query, time_range, language='en', region=None, logger=None):
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
    request_news(query, tbs, news_list, language, region, logger)
    
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
            return "failed: Empty content extracted"
        
        return text
    except requests.HTTPError as e:
        # 403/404 errors are common when scraping, so we can log them as warnings instead of errors
        if logger:
            status = e.response.status_code if e.response is not None else "?"
            logger.warning(f"HTTP {status} for {url}")
        return f"failed: HTTP {status} for {url}"
    except Exception as e:
        if logger:
            logger.error(f"Error fetching article content from {url}: {e}")
        return f"failed: Error fetching article content from {url}: {e}"
    
def remove_duplicates_missing(news_list):    
    df = pd.DataFrame(news_list)
    
    # remove duplicates based on url
    df = df.drop_duplicates(subset='link')
    
    # remove rows with missing or null values in the 'link' column
    df = df.dropna(subset=['link'])
    
    # convert back to news_list
    news_list = df.to_dict(orient='records')
    
    return news_list
    
def new_article(article,scraper, cursor, article_dicts, logger=None):
    article_content = fetch_article_content(article['link'], scraper, logger)
    article['content'] = article_content
    
    # insert the article into the database
    article_id = insert_articles_record(article, cursor, logger)
    
    if article_id:
        article_dicts[article_id] = article
    else:
        if logger:
            logger.error(f"Failed to insert article into database: {article['title']}")

def article_pipeline(query_list, time_range, language='en', region=None, logger=None):
    if logger is None:
        logger = get_logger()
    
    article_list = []
    for query in query_list:
        article_list.extend(collect_news(query, time_range, language, region, logger))
    
    # remove duplicates based on url
    article_list = remove_duplicates_missing(article_list)
    
    # convert relative dates to absolute dates in the news list
    article_list = convert_news_date(article_list)
    
    # restructure the news list
    article_list = restructure_news_list(article_list)
    
    # fetch the full article content for each news item
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )    
    
    article_dicts = {}
    to_fetch_articles = []
    to_embedding_articles = []
    
    with connect_to_postgres() as conn:
        with conn:
            cursor = conn.cursor(row_factory=dict_row)
            for article in article_list:
                link = article.get('link')
                
                # check if the article already exists in the database and already embedded
                existing_article = check_article_exists_embedded(cursor, link)
                
                if not existing_article:
                    new_article(article, scraper, cursor, article_dicts, logger)
                    
                            
                    

    
    article_ids_dict = get_articles_id(news_list)
    
    return article_ids_dict