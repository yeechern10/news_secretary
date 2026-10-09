from pathlib import Path

# db
db_dir = Path(__file__).parent / "db"
db_dir.mkdir(parents=True, exist_ok=True)
sqlite_db_path = db_dir / "news.db"

# news
NEWS_SOURCE = "https://serper.dev/news"  # News API endpoint

# llm
base_url = "http://localhost:11434/v1/"
chat_agent_model = "maternion/minicpm5:2b"
article_summarizer_model = "gemma3:4b"
news_summary_agent_model = "gemma3:4b"