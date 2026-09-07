import os
import re
import requests

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. LOAD ENVIRONMENT
# ==========================================

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "codebase_chunks_v2"
)


# ==========================================
# 2. EMBEDDING MODEL
# ==========================================

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ==========================================
# 3. FILENAME EXTRACTION
# ==========================================

def extract_filename(query: str):

    matches = re.findall(
        r"\b[\w.-]+\.(?:py|js|jsx|ts|tsx|java|cpp|c|h|hpp|cs|go|rs|php|rb|swift|kt|kts|html|css|scss|json|yaml|yml|md|txt)\b",
        query,
        flags=re.IGNORECASE,
    )

    if matches:
        return matches[0].lower()

    return None


# ==========================================
# 4. SEARCH CODEBASE
# ==========================================

def search_codebase(
    query: str,
    limit: int = 3
):

    print("\n[QDRANT SEARCH]")
    print("Query:", query)

    target_filename = extract_filename(
        query
    )

    if target_filename:

        print(
            "Detected filename:",
            target_filename
        )

    else:

        print(
            "Detected filename: None"
        )

    # --------------------------------------
    # Create query embedding
    # --------------------------------------

    query_vector = embedding_model.encode(
        query
    ).tolist()

    # --------------------------------------
    # Qdrant REST endpoint
    # --------------------------------------

    url = (
        f"{QDRANT_URL}"
        f"/collections/{COLLECTION_NAME}"
        f"/points/query"
    )

    headers = {
        "api-key": QDRANT_API_KEY,
        "Content-Type": "application/json",
    }

    # --------------------------------------
    # Build query
    # --------------------------------------

    payload = {

        "query": query_vector,

        "limit": min(
            max(limit, 1),
            20
        ),

        "with_payload": True,

    }

    # --------------------------------------
    # Filename filter
    # --------------------------------------

    if target_filename:

        payload["filter"] = {

            "must": [

                {

                    "key": "file_name",

                    "match": {

                        "value": target_filename

                    }

                }

            ]

        }

    # --------------------------------------
    # Send request
    # --------------------------------------

    response = requests.post(

        url,

        headers=headers,

        json=payload,

        timeout=60,

    )

    # --------------------------------------
    # Debug error
    # --------------------------------------

    if response.status_code != 200:

        print(
            "\nQDRANT ERROR:"
        )

        print(
            response.text
        )

    response.raise_for_status()

    data = response.json()

    # --------------------------------------
    # Extract results
    # --------------------------------------

    results = data.get(
        "result",
        {}
    ).get(
        "points",
        []
    )

    retrieved = []

    for result in results:

        payload_data = result.get(
            "payload",
            {}
        )

        retrieved.append({

            "score": result.get(
                "score",
                0.0
            ),

            "content": payload_data.get(
                "content",
                ""
            ),

            "file_path": payload_data.get(
                "file_path",
                ""
            ),

            "file_name": payload_data.get(
                "file_name",
                ""
            ),

            "chunk_index": payload_data.get(
                "chunk_index",
                -1
            ),

        })

    # --------------------------------------
    # Sort filename results by source order
    # --------------------------------------

    if target_filename and retrieved:

        retrieved.sort(

            key=lambda x: x.get(
                "chunk_index",
                0
            )

        )

        print(

            f"Found {len(retrieved)} "
            f"chunk(s) from "
            f"{target_filename}"

        )

    # --------------------------------------
    # Final limit
    # --------------------------------------

    retrieved = retrieved[:limit]

    print(
        f"Retrieved "
        f"{len(retrieved)} code chunks"
    )

    # --------------------------------------
    # Print results
    # --------------------------------------

    for i, result in enumerate(
        retrieved,
        1
    ):

        print(

            f"  {i}. "
            f"{result.get('file_name', 'unknown')} "
            f"(chunk="
            f"{result.get('chunk_index', -1)}, "
            f"score="
            f"{result.get('score', 0.0):.8f})"

        )

    return retrieved


# ==========================================
# 5. TEST
# ==========================================

if __name__ == "__main__":

    results = search_codebase(

        "What functions are defined in nodes.py?",

        limit=10

    )

    print(
        "\n=============================="
    )

    print(
        "RETRIEVED CODE"
    )

    print(
        "=============================="
    )

    for i, result in enumerate(
        results,
        1
    ):

        print(
            f"\n--- Result {i} ---"
        )

        print(
            "Score:",
            result["score"]
        )

        print(
            "File:",
            result["file_name"]
        )

        print(
            "Chunk:",
            result["chunk_index"]
        )

        print(
            "\nCode:"
        )

        print(
            result["content"][:1000]
        )