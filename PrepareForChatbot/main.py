import os
from PrepareForChatbot.chunking import chunk_text
from PrepareForChatbot.chroma_store import save_chunks_to_chroma

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

GUIDE_DIR = os.path.join(BASE_DIR, "GuideForChatbot")

def load_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    about_text = load_txt(os.path.join(GUIDE_DIR, "about_app.txt"))
    account_text = load_txt(os.path.join(GUIDE_DIR, "account_help.txt"))

    about_chunks = chunk_text(about_text)
    account_chunks = chunk_text(account_text)

    save_chunks_to_chroma(about_chunks, source="about_app")
    save_chunks_to_chroma(account_chunks, source="account_help")

    print("✅ Embedded & saved to ChromaDB")
