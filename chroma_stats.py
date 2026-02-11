"""
Print ChromaDB stats for current persisted entries.
Shows total chunks, unique files, and chunks per file.
"""
from core.vector_store import vector_store_manager
from collections import Counter


def main():
    if not vector_store_manager.is_available():
        print("Chroma vector store is not available.")
        return

    collection = vector_store_manager.collection
    results = collection.get(include=["metadatas"]) or {}
    ids = results.get("ids", []) or []
    metadatas = results.get("metadatas", []) or []

    total_chunks = len(ids)
    print(f"Persist dir: {vector_store_manager.persist_directory}")
    print(f"Collection: {vector_store_manager.collection_name}")
    print(f"Total chunks: {total_chunks}")

    if not metadatas:
        print("No metadata found.")
        return

    counts = Counter()
    for meta in metadatas:
        filename = (meta or {}).get("filename", "<missing filename>")
        counts[filename] += 1

    print(f"Total unique files: {len(counts)}")
    print("\nChunks per file:")
    for filename, count in sorted(counts.items(), key=lambda x: x[0]):
        print(f"- {filename}: {count}")


if __name__ == "__main__":
    main()

