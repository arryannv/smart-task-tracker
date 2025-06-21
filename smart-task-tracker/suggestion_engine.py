import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def suggest_tasks():
    conn = sqlite3.connect('tasks.db')

    completed_df = pd.read_sql_query("SELECT * FROM tasks WHERE done = 1", conn)
    pending_df = pd.read_sql_query("SELECT * FROM tasks WHERE done = 0", conn)

    conn.close()

    if completed_df.empty or pending_df.empty:
        return []

    # Combine text info
    completed_df['text'] = completed_df['title'] + ' ' + completed_df['description'].fillna('') + ' ' + completed_df['category'] + ' ' + completed_df['priority']
    pending_df['text'] = pending_df['title'] + ' ' + pending_df['description'].fillna('') + ' ' + pending_df['category'] + ' ' + pending_df['priority']

    # Fit TF-IDF on both
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(pd.concat([completed_df['text'], pending_df['text']]))

    # Separate the matrices
    completed_tfidf = tfidf_matrix[:len(completed_df)]
    pending_tfidf = tfidf_matrix[len(completed_df):]

    # Similarity between pending and completed
    sim_scores = cosine_similarity(pending_tfidf, completed_tfidf)

    # Get average similarity score of each pending task
    avg_scores = sim_scores.mean(axis=1)

    # Get top 5 recommended tasks
    top_indices = avg_scores.argsort()[::-1][:5]

    return pending_df.iloc[top_indices].to_dict(orient='records')
