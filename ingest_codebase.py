# Codebase ingestion module
# This file handles codebase ingestion.
import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. ENVIRONMENT
# ==========================================

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "codebase_chunks_v2"

PROJECT_ROOT = Path(__file__).resolve().parent

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
VECTOR_SIZE = 384

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php", ".rb",
    ".swift", ".kt", ".kts",
    ".html", ".css", ".scss",
    ".json", ".yaml", ".yml",
    ".md", ".txt",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
}


# ==========================================
# 2. VALIDATE ENVIRONMENT
# ==========================================

if not QDRANT_URL:
    raise ValueError("QDRANT_URL is missing in .env")

if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY is missing in .env")


# ==========================================
# 3. EMBEDDING MODEL
# ==========================================

print("\nLoading embedding model...")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ==========================================
# 4. FIND PROJECT FILES
# ==========================================

def get_project_files():

    files = []

    for file_path in PROJECT_ROOT.rglob("*"):

        if not file_path.is_file():
            continue

        if any(
            part in IGNORED_DIRECTORIES
            for part in file_path.parts
        ):
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        if file_path.name == ".env":
            continue

        files.append(file_path)

    return sorted(files)


# ==========================================
# 5. READ FILE
# ==========================================

def read_file(file_path):

    try:

        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:

        print(
            f"Could not read {file_path}: {e}"
        )

        return ""


# ==========================================
# 6. CHUNK TEXT
# ==========================================

def chunk_text(text):

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + CHUNK_SIZE

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - CHUNK_OVERLAP

    return chunks


# ==========================================
# 7. CREATE QDRANT COLLECTION
# ==========================================

def create_collection():

    url = (
        f"{QDRANT_URL}"
        f"/collections/{COLLECTION_NAME}"
    )

    headers = {
        "api-key": QDRANT_API_KEY,
        "Content-Type": "application/json",
    }

    # Delete old collection if it exists
    print(
        f"\nChecking collection: "
        f"{COLLECTION_NAME}"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    if response.status_code == 200:

        print("Existing collection found.")
        print("Deleting old collection...")

        delete_response = requests.delete(
            url,
            headers=headers,
            timeout=30
        )

        delete_response.raise_for_status()

        print("Old collection deleted.")

    elif response.status_code != 404:

        response.raise_for_status()

    # Create fresh collection
    print("Creating fresh collection...")

    payload = {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine",
        }
    }

    create_response = requests.put(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    create_response.raise_for_status()

    print(
        f"Collection created: "
        f"{COLLECTION_NAME}"
    )


# ==========================================
# 8. MAIN INGESTION
# ==========================================

def main():

    print("\n====================================")
    print("FRESH CODEBASE INGESTION")
    print("====================================")

    print("\nProject root:")
    print(PROJECT_ROOT)

    # --------------------------------------
    # Create fresh collection
    # --------------------------------------

    create_collection()

    # --------------------------------------
    # Find files
    # --------------------------------------

    files = get_project_files()

    print(
        f"\nFound {len(files)} project files."
    )

    # --------------------------------------
    # Read + chunk
    # --------------------------------------

    all_chunks = []

    for file_path in files:

        content = read_file(file_path)

        if not content.strip():
            continue

        relative_path = file_path.relative_to(
            PROJECT_ROOT
        )

        chunks = chunk_text(content)

        print(
            f"{relative_path} -> "
            f"{len(chunks)} chunks"
        )

        for index, chunk in enumerate(chunks):

            all_chunks.append({
                "content": chunk,
                "file_name": file_path.name,
                "file_path": str(relative_path),
                "chunk_index": index,
            })

    print(
        f"\nTotal chunks: "
        f"{len(all_chunks)}"
    )

    if not all_chunks:
        print("No chunks found.")
        return

    # --------------------------------------
    # Generate embeddings
    # --------------------------------------

    print("\nGenerating embeddings...")

    texts = [
        item["content"]
        for item in all_chunks
    ]

    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    print("Embeddings generated.")

    # --------------------------------------
    # Upload to Qdrant
    # --------------------------------------

    print("\nUploading to Qdrant...")

    upload_url = (
        f"{QDRANT_URL}"
        f"/collections/{COLLECTION_NAME}"
        f"/points?wait=true"
    )

    headers = {
        "api-key": QDRANT_API_KEY,
        "Content-Type": "application/json",
    }

    batch_size = 50

    for i in range(
        0,
        len(all_chunks),
        batch_size
    ):

        batch = all_chunks[
            i:i + batch_size
        ]

        points = []

        for j, item in enumerate(batch):

            global_index = i + j

            points.append({
                "id": str(uuid.uuid4()),
                "vector": embeddings[
                    global_index
                ].tolist(),
                "payload": item,
            })

        response = requests.put(
            upload_url,
            headers=headers,
            json={
                "points": points
            },
            timeout=60,
        )

        response.raise_for_status()

        uploaded = min(
            i + batch_size,
            len(all_chunks)
        )

        print(
            f"Uploaded "
            f"{uploaded}/"
            f"{len(all_chunks)}"
        )

    # --------------------------------------
    # Final verification
    # --------------------------------------

    print("\n====================================")
    print("INGESTION COMPLETED")
    print("====================================")

    print(
        f"\nCollection: "
        f"{COLLECTION_NAME}"
    )

    print(
        f"Files: "
        f"{len(files)}"
    )

    print(
        f"Chunks: "
        f"{len(all_chunks)}"
    )


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()