# Similarity Tool Module

import json
import numpy as np
import ast


from tools.postgres_tool import get_user_profile
from tools.db_utils import execute_postgres_query


try:
    from tools.logger_utils import get_logger, set_run_id
except ImportError:
    from logger_utils import get_logger, set_run_id

logger = get_logger(__name__, "similarity_tool.log")




def cosine_distance(vec1:list, vec2:list) -> float:
    """Calculate cosine distance between two vectors."""
    if not vec1 or not vec2:
        return float('inf')  # Return infinity if either vector is empty
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return float('inf')  # Avoid division by zero
    cosine_similarity = dot_product / (norm_vec1 * norm_vec2)
    return round(float(1 - cosine_similarity), 4)  # Convert similarity to distance


def similarity_tool(postgres_tool_output:str) -> str:


    try:
        logger.info("Starting similarity_tool")
        data = json.loads(postgres_tool_output)
        profile_vector = data["profile_vector"]
        purchased_ipo_ids = tuple(data["purchased_ipo_ids"])
        logger.debug("Received %d purchased IPO ids", len(purchased_ipo_ids))

        #print("Profile Vector:", profile_vector)

        required_tuples= execute_postgres_query(
        query="SELECT ipo_id, name, embedding FROM ipo WHERE ipo_id NOT IN %s;",
        params=(tuple(purchased_ipo_ids),))
        logger.debug("Fetched %d IPO rows for similarity comparison", len(required_tuples))


        distances = []

        for row in required_tuples:
            ipo_id=row[0]
            name=row[1]
            embedding_str=row[2]
            embedding = ast.literal_eval(embedding_str)  # Convert string back to list
            #print("Profile Vector:", profile_vector)
            #print("embedding:", embedding)

            #case when the the vector is zero
            if all(v == 0 for v in embedding):
                logger.debug("Skipping IPO %s because embedding is zero vector", name)
                continue  # Skip this IPO if the embedding is a zero vector because why would domeone invest in an ipo with zero vector embedding or smallest financial embeddings
            
            distnance = cosine_distance(profile_vector, embedding)
            #print("Distance:", distnance,"\n")

            distances.append((ipo_id, name, distnance))

        #print("Distances:", distances)
        # Sort by distance and get bottom 4 (most similar)
        distances.sort(key=lambda x: x[2])  
        top_5 = distances[:4]
        logger.info("Computed top %d similar IPO candidates", len(top_5))
        #print("Top 5 Similar IPOs:", top_5)

        return json.dumps({
                "success": True,
                "source": "similarity_tool",
                "candidates": [
                    {
                        "ipo_id": row[0],
                        "name": row[1],
                        "knn_distance": row[2]
                    }
                    for row in top_5
                ]
            })
    except Exception as e:
            logger.exception("similarity_tool failed")
            return json.dumps({
                    "success": False,
                    "source": "knn",
                    "candidates": [],
                    "error": str(e)
                })
                



'''

if __name__ == "__main__":
    set_run_id()
    postgres_output = get_user_profile("0x32Be343B94f860124dC4fEe278FDCBD38C102D88")
    print(similarity_tool(postgres_output))
'''