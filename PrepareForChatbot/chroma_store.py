from PrepareForChatbot.chroma_client import get_chroma_client
from PrepareForChatbot.embedding import embed_text
import os

chroma_client = get_chroma_client()

collection = chroma_client.get_or_create_collection(
    name="chatbot_docs"
)

def save_chunks_to_chroma(chunks: list[str], source: str):
    embeddings = []
    ids = []
    metadatas = []

    for idx, chunk in enumerate(chunks):
        vector = embed_text(chunk)
        embeddings.append(vector)
        ids.append(f"{source}_{idx}")
        metadatas.append({
            "source": source,
            "chunk_index": idx
        })

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    print(f"✅ Saved {len(chunks)} chunks from {source}")