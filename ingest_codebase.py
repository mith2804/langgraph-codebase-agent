import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. LOAD ENVIRONMENT
# ==========================================

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Fresh collection to avoid stale data
COLLECTION_NAME = "codebase_chunks_v2"

PROJECT_ROOT = Path(__file__).resolve().parent


# ==========================================
# 2. SETTINGS
# ==========================================

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

VECTOR_SIZE = 384

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".html",
    ".css",
    ".scss",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}


# ==========================================
# 3. EMBEDDING MODEL
# ==========================================

print("\nLoading embedding model...")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ==========================================
# 4. QDRANT HEADERS
# ==========================================

headers = {
    "api-key": QDRANT_API_KEY,
    "Content-Type": "application/json",
}


# ==========================================
# 5. CREATE FRESH COLLECTION
# ==========================================

def create_collection():

    print(
        f"\nPreparing collection: {COLLECTION_NAME}"
    )

    collection_url = (
        f"{QDRANT_URL}"
        f"/collections/{COLLECTION_NAME}"
    )

    # Check whether collection already exists
    response = requests.get(
        collection_url,
        headers=headers,
        timeout=60,
    )

    if response.status_code == 200:

        print(
            "Collection already exists."
        )

        print(
            "Deleting old version..."
        )

        delete_response = requests.delete(
            collection_url,
            headers=headers,
            timeout=60,
        )

        delete_response.raise_for_status()

        print(
            "Old collection deleted."
        )

    elif response.status_code != 404:

        response.raise_for_status()

    # Create fresh collection
    print(
        "Creating fresh collection..."
    )

    create_response = requests.put(
        collection_url,
        headers=headers,
        json={
            "vectors": {
                "size": VECTOR_SIZE,
                "distance": "Cosine",
            }
        },
        timeout=60,
    )

    create_response.raise_for_status()

    print(
        f"Collection created: {COLLECTION_NAME}"
    )


# ==========================================
# 6. FIND PROJECT FILES
# ==========================================

def get_project_files():

    files = []

    for path in PROJECT_ROOT.rglob("*"):

        if not path.is_file():
            continue

        # Ignore unwanted directories
        if any(
            directory in path.parts
            for directory in IGNORED_DIRECTORIES
        ):
            continue

        # Only supported source/document files
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        files.append(path)

    return sorted(files)


# ==========================================
# 7. READ FILE
# ==========================================

def read_file(path):

    try:

        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    except Exception as e:

        print(
            f"Could not read {path}: {e}"
        )

        return ""


# ==========================================
# 8. CHUNK TEXT
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

        start = end - CHUNK_OVERLAP

    return chunks


# ==========================================
# 9. MAIN INGESTION
# ==========================================

def main():

    print("\n====================================")
    print("FRESH CODEBASE INGESTION")
    print("====================================")

    print(
        "\nProject root:"
    )

    print(PROJECT_ROOT)

    # --------------------------------------
    # Create fresh Qdrant collection
    # --------------------------------------

    create_collection()

    # --------------------------------------
    # Find files
    # --------------------------------------

    files = get_project_files()

    print(
        f"\nFound {len(files)} project files."
    )

    all_chunks = []

    # --------------------------------------
    # Read + chunk files
    # --------------------------------------

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

                "file_path": str(
                    relative_path
                ),

                "chunk_index": index,

            })

    print(
        f"\nTotal chunks: "
        f"{len(all_chunks)}"
    )

    if not all_chunks:

        print(
            "\nNo code files found."
        )

        return

    # ======================================
    # CREATE EMBEDDINGS
    # ======================================

    print(
        "\nCreating embeddings..."
    )

    texts = [
        item["content"]
        for item in all_chunks
    ]

    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=True,
    )

    print(
        "Embeddings created."
    )

    # ======================================
    # PREPARE QDRANT POINTS
    # ======================================

    points = []

    for item, vector in zip(
        all_chunks,
        embeddings,
    ):

        points.append({

            "id": str(
                uuid.uuid4()
            ),

            "vector": vector.tolist(),

            "payload": {

                "content": item[
                    "content"
                ],

                "file_name": item[
                    "file_name"
                ],

                "file_path": item[
                    "file_path"
                ],

                "chunk_index": item[
                    "chunk_index"
                ],

            },

        })

    # ======================================
    # UPLOAD IN BATCHES
    # ======================================

    print(
        "\nUploading to Qdrant..."
    )

    upload_url = (
        f"{QDRANT_URL}"
        f"/collections/{COLLECTION_NAME}"
        f"/points?wait=true"
    )

    batch_size = 50

    for i in range(
        0,
        len(points),
        batch_size,
    ):

        batch = points[
            i:i + batch_size
        ]

        response = requests.put(
            upload_url,
            headers=headers,
            json={
                "points": batch
            },
            timeout=60,
        )

        response.raise_for_status()

        uploaded = min(
            i + batch_size,
            len(points),
        )

        print(
            f"Uploaded "
            f"{uploaded}/{len(points)}"
        )

    # ======================================
    # FINAL CHECK
    # ======================================

    print(
        "\n===================================="
    )

    print(
        "INGESTION COMPLETED"
    )

    print(
        "===================================="
    )

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
        f"{len(points)}"
    )


if __name__ == "__main__":

    main()