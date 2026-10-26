import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# db
DB_DIR = Path(__file__).parent.parent / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

# postgres
username = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
db_name = os.getenv("POSTGRES_DB", "news_secretary")
PG_CONNECTION_STRING = f"postgresql://{username}:{password}@localhost:5432/news_secretary"

# table names
TABLE_NAMES = {
    "users": "users",
    "articles": "articles",
    "events": "events",
    "keywords": "keywords",
    "user_keywords": "user_keywords",
    "user_article_interactions": "user_article_interactions",
    "user_event_interactions": "user_event_interactions",
    "event_article_relationships": "event_article_relationships",
    "events_keywords_relationships": "events_keywords_relationships"
}


# keywords
KEYWORDS_FILE_PATH = Path(__file__).parent.parent / "db" / "keywords.json"

# news
NEWS_SOURCE = "https://google.serper.dev/news"  # News API endpoint

# llm
CHAT_AGENT_BASE_URL = "http://localhost:11434/v1/"
CHAT_AGENT_MODEL = "maternion/minicpm5:2b"

EVENT_DETECTOR_BASE_URL = "http://localhost:11434/v1/"
EVENT_DETECTOR_MODEL = "gemma3:4b"

ARTICLE_SUMMARIZER_BASE_URL = "http://localhost:11434/v1/"
ARTICLE_SUMMARIZER_MODEL = "gemma3:4b"

NEWS_SUMMARY_AGENT_BASE_URL = "http://localhost:11434/v1/"
NEWS_SUMMARY_AGENT_MODEL = "gemma3:4b"


# context lengths
MAX_ARTICLE_TOKENS = 8000  # Maximum length of the article content to be summarized

# uncertain article reanalysis
UNCERTAIN_ARTICLE_REANALYSIS_CONTENT_TRUNCATE = 2000  # Maximum length of the article content to be reanalyzed