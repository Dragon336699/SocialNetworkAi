from PrepareForChatbot.chroma_client import get_chroma_client
from PrepareForChatbot.embedding import embed_text

chroma_client = get_chroma_client()
collection = chroma_client.get_collection("chatbot_docs")
query = "Muốn đổi mật khẩu thì sao?"
query_embedding = embed_text(query)

def test_query():
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    print("\n📌 Documents:")
    for doc in result["documents"][0]:
        print("-" * 40)
        print(doc)

    print("\n📌 Metadata:")
    print(result["metadatas"][0])

if __name__ == "__main__":
    test_query()
