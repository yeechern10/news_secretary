from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


from ..db.retrieve import retrieve_leaves_keywords_from_db, structure_keywords
from ..configuration import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE

def keyword_dicts_to_text(keyword_dicts):
    keywords_texts = []
    for _, details in keyword_dicts.items():
        keyword_name = details["keyword"]
        keyword_description = details["description"]
        keyword_synonyms = details["synonyms"]
        parents = []
        parent_id = details["parent_id"]
        while parent_id:
            parent_details = keyword_dicts.get(parent_id)
            if parent_details:
                parents.append(parent_details["keyword"])
                parent_id = parent_details["parent_id"]
            else:
                break
        
        text = f"{keyword_name}\n{keyword_description}:{', '.join(keyword_synonyms)}\n{' > '.join(parents[::-1])}\n"
        keywords_texts.append(text)
    return keywords_texts

def embedding_keywords(keyword_dicts):
    keywords_texts = keyword_dicts_to_text(keyword_dicts)
    
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": EMBEDDING_BATCH_SIZE,
        }
    )

    doc_vectors = embedding.embed_documents(keywords_texts)
    for i, keyword_id in enumerate(keyword_dicts.keys()):
        keyword_dicts[keyword_id]["vector"] = doc_vectors[i]
    
    return keyword_dicts

def article_dicts_to_text(article_dicts):
    articles_texts = []
    for _, details in article_dicts.items():
        article_title = details["title"]
        article_content = details["content"]
        if article_content.startswith("failed:"):
            article_content = " "
        text = f"{article_title}\n{article_content}\n"
        articles_texts.append(text)
    return articles_texts

def embedding_articles(article_dicts):
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": EMBEDDING_BATCH_SIZE,
        }
    )

    article_vectors = embedding.embed_documents([article["content"] for article in article_dicts.values()])
    
    for i, article_id in enumerate(article_dicts.keys()):
        article_dicts[article_id]["vector"] = article_vectors[i]
    
    return article_dicts