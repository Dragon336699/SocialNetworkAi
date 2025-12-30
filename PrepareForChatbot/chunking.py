def chunk_text (text: str, chunk_size=400, overlap =80):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start < 0:
            start  = 0
    return chunks

def load_and_chunk_about_app():
    with open("../GuideForChatbot/about_app.txt", "r", encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {i} ---")
        print(chunk)
    return chunks

def load_and_chunk_account_help():
    with open("../GuideForChatbot/account_help.txt", "r", encoding="utf-8") as f:
        text = f.read()
    chunks = chunk_text(text)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {i} ---")
        print(chunk)
    return chunks

if __name__ == "__main__":
    about_chunks = load_and_chunk_about_app()
    account_chunks = load_and_chunk_account_help()