import requests

from ....comfiguration import NEWS_SOURCE

def request_news(query, time_range, serper_api_key, news_list,language ='en', region = None, location = None,logger = None):
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
            "location": location,
            "hl": language,
            "tbs": time_range
        }
    )

    if response.status_code == 200:
        search_results = response.json()
        news_list.extend(search_results.get('news', []))
    else:
        if logger:
            logger.error(f"Search request failed with status code {response.status_code} and message: {response.text}")
        else:
            print(f"Search request failed with status code {response.status_code} and message: {response.text}")