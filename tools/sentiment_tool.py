# Sentiment Tool Module

import json
import feedparser
from transformers import pipeline
from urllib.parse import quote_plus
from cache import news_cache
from postgres_tool import get_user_profile
from similarity_tool import similarity_tool
from top_ipo_tool import top_ipo_tool

# Load FinBERT model once at startup
finbert = pipeline(
    "text-classification",
    model="ProsusAI/finbert",
    top_k=None,  # get all labels
)


def fetch_news(company_name: str) -> list:
    """Fetch recent news headlines for a company from Google News RSS."""
    query = quote_plus(f"{company_name}")
    url = f"https://news.google.com/rss/search?q={query}+IPO&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    headlines = [entry.title for entry in feed.entries[:10]]

    return headlines


def compute_sentiment_score(headlines: list) -> float:
    """Use FinBERT to compute sentiment score from headlines."""
    if not headlines:
        return 0.5  # neutral if no news
    
    scores = []
    for headline in headlines:
        result = finbert(headline[:512])[0]  # truncate to model max
        score_map = {item['label']: item['score'] for item in result}
        # Convert to scalar: positive - negative shifted to 0-1 range
        raw = score_map.get('positive', 0) - score_map.get('negative', 0)
        normalized = round((raw + 1) / 2, 4)  # maps [-1,1] to [0,1]
        scores.append(normalized)

    return round(sum(scores) / len(scores), 4)  # average across headlines



def sentiment_tool(candidates_output: str) -> str:
    """Takes output from similarity_tool or top_ipo_tool,
    fetches news, scores sentiment using FinBERT,
    computes composite score and returns ordered candidates."""
    try:
        data = json.loads(candidates_output)
        candidates = data["candidates"]

        scored_candidates = []
        for candidate in candidates:
            ipo_id = candidate["ipo_id"]
            name = candidate["name"]
            knn_distance = candidate["knn_distance"]

            # Fetch news
            headlines = fetch_news(name)

            # Store in cache
            news_cache[name] = headlines
            #print("\n",f"Fetched news for {name}: {headlines}","\n")

            # Compute sentiment score using FinBERT
            sentiment_score = compute_sentiment_score(headlines)
            #print(f"{name} -> sentiment: {sentiment_score}")

            # Compute composite score
            knn_similarity = 1 - knn_distance
            composite_score = round((0.7 * knn_similarity) + (0.3 * sentiment_score), 4)
            #print(f"{name} -> knn_similarity: {knn_similarity}, composite_score: {composite_score}")

            try:
                #print("adding candidate")
                scored_candidates.append({
                    "ipo_id": ipo_id,
                    "name": name,
                    "knn_distance": knn_distance,
                    "sentiment_score": sentiment_score,
                    "composite_score": composite_score
                })
                #print(scored_candidates)

            except Exception as e:
                print(f"Error processing candidate {name}: {e}")
                continue

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

        # Add rank
        for i, candidate in enumerate(scored_candidates):
            candidate["rank"] = i + 1

        #print("\n","Final scored candidates:", scored_candidates,"\n")

        return json.dumps({
            "success": True,
            "candidates": scored_candidates
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "candidates": [],
            "error": str(e)
        })


if __name__ == "__main__":
    print("Testing sentiment_tool with top IPOs for a user profile...\n")
    postgres_output = get_user_profile("0x2b3c4d5e6f7890abcdef1234567890abcdef1234")
    print("SIMILARTIY TOOL OUTPUT",similarity_tool(postgres_output))
    print("\nSENTIMENT TOOL OUTPUT",sentiment_tool(similarity_tool(postgres_output)))
    