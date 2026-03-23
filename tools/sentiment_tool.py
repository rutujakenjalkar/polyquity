# Sentiment Tool Module

import json
import feedparser
from transformers import pipeline
from urllib.parse import quote_plus
from cache import news_cache
from postgres_tool import get_user_profile
from similarity_tool import similarity_tool
from top_ipo_tool import top_ipo_tool
try:
    from tools.logger_utils import get_logger, set_run_id
except ImportError:
    from logger_utils import get_logger, set_run_id

logger = get_logger(__name__, "sentiment_tool.log")

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
    logger.debug("Fetched %d headlines for %s", len(headlines), company_name)

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
        logger.info("Starting sentiment_tool")
        data = json.loads(candidates_output)
        candidates = data["candidates"]
        logger.debug("Received %d candidates for sentiment scoring", len(candidates))

        scored_candidates = []
        for candidate in candidates:
            ipo_id = candidate["ipo_id"]
            name = candidate["name"]
            knn_distance = candidate["knn_distance"]

            # Fetch news
            headlines = fetch_news(name)

            # Store in cache
            news_cache[name] = headlines
            logger.debug("Stored %d headlines in cache for %s", len(headlines), name)

            # Compute sentiment score using FinBERT
            sentiment_score = compute_sentiment_score(headlines)
            logger.debug("%s sentiment score: %.4f", name, sentiment_score)

            # Compute composite score
            knn_similarity = 1 - knn_distance
            composite_score = round((0.5*knn_similarity) + (0.5 * sentiment_score), 4)
            logger.debug(
                "%s knn_similarity=%.4f composite_score=%.4f",
                name,
                knn_similarity,
                composite_score,
            )

            try:
                scored_candidates.append({
                    "ipo_id": ipo_id,
                    "name": name,
                    "knn_distance": knn_distance,
                    "sentiment_score": sentiment_score,
                    "composite_score": composite_score
                })
                logger.debug("Added scored candidate for %s", name)

            except Exception as e:
                logger.exception("Error processing candidate %s", name)
                continue

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

        # Add rank
        for i, candidate in enumerate(scored_candidates):
            candidate["rank"] = i + 1

        logger.info("Completed sentiment scoring for %d candidates", len(scored_candidates))

        return json.dumps({
            "success": True,
            "candidates": scored_candidates
        })

    except Exception as e:
        logger.exception("sentiment_tool failed")
        return json.dumps({
            "success": False,
            "candidates": [],
            "error": str(e)
        })


if __name__ == "__main__":
    set_run_id()
    print("Testing sentiment_tool with top IPOs for a user profile...\n")
    postgres_output = get_user_profile("0x2b3c4d5e6f7890abcdef1234567890abcdef1234")
    print("SIMILARTIY TOOL OUTPUT",similarity_tool(postgres_output))
    print("\nSENTIMENT TOOL OUTPUT",sentiment_tool(similarity_tool(postgres_output)))
    print("Testing sentiment_tool with top IPOs for new user...\n")
    
