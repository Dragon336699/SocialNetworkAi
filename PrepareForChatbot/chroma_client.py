import os
import chromadb

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

CHROMA_DIR = os.path.join(ROOT_DIR, "chroma_db")

def get_chroma_client():
    return chromadb.PersistentClient(
        path=CHROMA_DIR
    )
