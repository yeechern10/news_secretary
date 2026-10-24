from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from ..db.retrieve import retrieve_leaves_keywords_from_db, structure_keywords

def keywords_structure_to_text(keyword_dict):
    keywords_texts = []
    for _, details in keyword_dict.items():
        keyword_name = details["keyword"]
        keyword_description = details["description"]
        keyword_synonyms = details["synonyms"]
        parents = []
        parent_id = details["parent_id"]
        while parent_id:
            parent_details = keyword_dict.get(parent_id)
            if parent_details:
                parents.append(parent_details["keyword"])
                parent_id = parent_details["parent_id"]
            else:
                break
        
        text = f"{keyword_name}\n{keyword_description}\{', '.join(keyword_synonyms)}\n{' > '.join(parents[::-1])}\n"
        keywords_texts.append(text)
    return keywords_texts

def text_keywords_vector_similarity(events, language="en", top_k= 20):
    keywords = retrieve_leaves_keywords_from_db()
    keyword_dict = structure_keywords(keywords)
    keywords_texts = keywords_structure_to_text(keyword_dict)
    
    if language == "zh":
        vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 4),
            min_df=1,
        )
    else:
        vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 3),
            min_df=1,
        )

    tfidf_matrix = vectorizer.fit_transform(keywords_texts)
    
    # Compute the cosine similarity between the events title, summary and each keyword
    for event in events:
        event_text = f"{event['title']} {event['summary']}"
        text_tfidf = vectorizer.transform([event_text])
        similarities = linear_kernel(text_tfidf, tfidf_matrix).ravel()
        top_indices = similarities.argsort()[::-1][-top_k:]
        
        if event.get('keywords') is None:
            event['keywords'] = []

        for i in top_indices:
            id = keywords[i][0]
            event['keywords'].append({
                "id": id,
                "name": keyword_dict[id]["keyword"],
                "description": keyword_dict[id]["description"],
                "synonyms": keyword_dict[id]["synonyms"],
                "parent_id": keyword_dict[id]["parent_id"],
                "child_ids": keyword_dict[id]["child_ids"],
                "created_at": keyword_dict[id]["created_at"],
                "similarity_score": similarities[i]
            })