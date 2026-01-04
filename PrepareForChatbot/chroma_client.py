import os
import chromadb

CHROMA_DIR = os.path.join("CHROMA_PATH", "./chroma_db")

def get_chroma_client():
    return chromadb.PersistentClient(
        path=CHROMA_DIR
    )
