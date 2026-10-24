import os
import json
import re
from openai import OpenAI
from bs4 import BeautifulSoup
import openai
import requests
import json
import cloudscraper
from transformers import AutoTokenizer
from huggingface_hub import login

from ..packages.collect_news import fetch_article_content
from .system_prompt import article_summarizer, article_summary_schema
from ..configuration import ARTICLE_SUMMARIZER_MODEL,  ARTICLE_SUMMARIZER_BASE_URL, MAX_ARTICLE_TOKENS

def model_to_hfmodel(model_name: str) -> str:
    # Mapping of model names to Hugging Face model identifiers
    model_mapping = {
        "gemma3:4b": "google/gemma-3-4b-it",
        "maternion/minicpm5:2b": "maternion/minicpm5:2b"
    }
    return model_mapping.get(model_name, None)

def limit_article_tokens(article, tokenizer, max_tokens, logger=None):
    try:
        tokens = tokenizer.encode(article, add_special_tokens=True)
        
        if len(tokens) > max_tokens:
            ellipsis_tokens = tokenizer.encode("...", add_special_tokens=False)
            
            limited_tokens = tokens[:max_tokens - len(ellipsis_tokens)] + ellipsis_tokens
            
            article = tokenizer.decode(limited_tokens, skip_special_tokens=True)
            
        if logger:
            logger.info(f"Article tokens limited to {len(limited_tokens)} tokens")
            
    except Exception as e:
        if logger:
            logger.error(f"Error limiting article tokens: {e}")
        else:
            print(f"Error limiting article tokens: {e}")
        
        # Fallback: truncate the article to max_tokens characters
        if len(article) > max_tokens*4:  # Assuming average 4 characters per token
            article = article[:max_tokens*4] + "..."
            if logger:
                logger.warning(f"Article truncated to {len(article)} characters as a fallback")

    
    return article

def summarize_article(llm_client, title, articles,keywords_list , source_name=None, published_at=None, language=None, logger=None):
    system_prompt = article_summarizer[list(article_summarizer.keys())[-1]]  # Get the last version of the system prompt
    
    user_prompt_json = {
        "user_preference_keywords": keywords_list,
        "title": title,
        "body": articles,
        "source_name": source_name,
        "published_at": published_at,
        "output_language": language if language else "english",
    }
    try:
        response = llm_client.chat.completions.create(
            model=ARTICLE_SUMMARIZER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt_json)}
            ],
            # response_format={"type": "json_object"},
            extra_body= {"format": article_summary_schema }
        )
        
    except openai.error.OpenAIError as e:
        if logger:
            logger.error(f"Error during summarization: {e}")
        else:
            print(f"Error during summarization: {e}")
        return None

    return response.choices[0].message.content

def summarize_articles(news_list, keywords_list, api_key, base_url=ARTICLE_SUMMARIZER_BASE_URL, logger=None):
    llm_client = OpenAI(api_key=api_key, base_url=base_url)
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    login(os.getenv("HF_TOKEN"), add_to_git_credential=True)
    tokenizer = AutoTokenizer.from_pretrained(model_to_hfmodel(ARTICLE_SUMMARIZER_MODEL))
    
    for news in news_list:
        title = news.get('title', '')
        content = news.get('content', '')
        source_name = news.get('source', None)
        published_at = news.get('date', None)
        source_url = news.get('link', None)
        language = news.get('language', None)

        # Fetch the full article content if the URL is provided
        if not source_url:
            news['summary'] = "failed: No source URL provided"
            continue  # Skip if no source URL is provided
        
        full_content = fetch_article_content(source_url, scraper, logger)
        if not full_content:
            news['summary'] = "failed: Unable to fetch article content"
            continue  # Skip if unable to fetch the article content
        
        content = limit_article_tokens(full_content, tokenizer, MAX_ARTICLE_TOKENS, logger)

        try:
            raw = summarize_article(llm_client, title, content, keywords_list, source_name, published_at, language, logger)
           
            # remove json formatting from the result_text
            result_text = raw.strip()
    
            # if the result is wrapped in ```json ... ``` , extract the content in the middle
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", result_text, re.DOTALL)
            if match:
                result_text = match.group(1).strip()

            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            if logger:
                logger.error(f"Error decoding JSON: {e}: {result_text}")
            else:
                print(f"Error decoding JSON: {e}: {result_text}")
            news['summary'] = "failed: Error decoding JSON"
            continue
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error: {e}")
            else:
                print(f"Unexpected error: {e}")
            news['summary'] = "failed: Unexpected error"
            continue
        
        news['summary'] = result.get('summary', 'No summary available')
        news['importance_score'] = result.get('importance_score', 0)
        news['keyword_relevance_scores'] = result.get('keyword_relevance_scores', {})
