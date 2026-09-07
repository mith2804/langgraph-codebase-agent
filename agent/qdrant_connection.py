import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient


load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "codebase_chunks")


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def test_qdrant():

    collections = client.get_collections()

    print("\n[QDRANT]")
    print("Connection successful!")

    print("Collections:")

    for collection in collections.collections:
        print("-", collection.name)


if __name__ == "__main__":
    test_qdrant()