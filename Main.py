import os
import joblib
import pandas as pd
from uuid import UUID
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from Database.database_sql import get_sql_connection
from Database.database_cassandra import get_cassandra_session

from Requests.CaptionRequest import CaptionRequest
from Requests.SummarizePostRequest import SummarizePostRequest
from Requests.QuestionRequest import QuestionRequest

from PrepareForChatbot.embedding import embed_text
from PrepareForChatbot.chroma_client import get_chroma_client
from llm_client import call_llm
from prompt import QA_PROMPT_TEMPLATE

from google import genai

# =====================
# ENV
# =====================
load_dotenv()

# =====================
# Lazy singletons
# =====================
_model = None
_chroma_collection = None
_llm_client = None


def get_model():
    global _model
    if _model is None:
        _model = joblib.load("friend_recommend_model.pkl")
    return _model


def get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is None:
        chroma_client = get_chroma_client()
        _chroma_collection = chroma_client.get_collection("chatbot_docs")
    return _chroma_collection


def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
    return _llm_client


# =====================
# Business logic
# =====================
def get_friend_list(user_id: UUID):
    sql = get_sql_connection()
    cursor = sql.cursor()

    rows = cursor.execute(
        "SELECT RelatedUserId FROM UserRelation WHERE user_id = ?",
        str(user_id)
    ).fetchall()

    return {UUID(r[0]) for r in rows}


def get_user_interaction(user_id: UUID):
    session = get_cassandra_session()

    counter_rows = session.execute(
        """
        SELECT target_user_id, view_count, search_count, like_count
        FROM user_interaction_counter WHERE user_id = %s
        """,
        (user_id,)
    )

    meta_rows = session.execute(
        """
        SELECT target_user_id, last_interaction
        FROM user_interaction_meta WHERE user_id = %s
        """,
        (user_id,)
    )

    meta_map = {
        r.target_user_id: r.last_interaction
        for r in meta_rows
    }

    now = datetime.utcnow()
    data = []

    for r in counter_rows:
        last = meta_map.get(r.target_user_id)
        last_days = (now - last.replace(tzinfo=None)).days if last else 999

        data.append({
            "target_user_id": r.target_user_id,
            "view_count": r.view_count or 0,
            "search_count": r.search_count or 0,
            "like_count": r.like_count or 0,
            "last_days": last_days
        })

    return pd.DataFrame(data)


def recommend_friends(user_id: UUID, top_k=10, threshold=0.6):
    df = get_user_interaction(user_id)
    if df.empty:
        return []

    friend_ids = get_friend_list(user_id)
    df = df[~df["target_user_id"].isin(friend_ids)]

    model = get_model()
    features = ["view_count", "search_count", "like_count", "last_days"]

    probs = model.predict_proba(df[features])[:, 1]
    df["probs"] = probs

    return (
        df[df["probs"] >= threshold]
        .sort_values("probs", ascending=False)
        .head(top_k)[["target_user_id", "probs"]]
        .to_dict(orient="records")
    )


def answer_question(question: str, top_k=3):
    collection = get_chroma_collection()

    query_embedding = embed_text(question)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    context = "\n\n".join(result["documents"][0])

    prompt = QA_PROMPT_TEMPLATE.format(
        context=context,
        question=question
    )

    return call_llm(prompt)


# =====================
# FastAPI app
# =====================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fricon.online",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# API
# =====================
@app.get("/ai/friend/recommend")
def recommend(user_id: UUID):
    return {
        "user_id": user_id,
        "recommendations": recommend_friends(user_id)
    }


@app.post("/ai/post/summary")
def summarize_post(req: SummarizePostRequest):
    client = get_llm_client()

    prompt = f"""
    Bạn là trợ lý tóm tắt nội dung bài viết mạng xã hội.
    Tóm tắt nội dung sau trong 3–5 dòng, trung lập.
    Nội dung:
    {req.content}
    """

    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {"data": res.text}


@app.post("/ai/post/rewrite")
def rewrite_post(req: CaptionRequest):
    client = get_llm_client()

    prompt = f"""
    Viết lại caption cho tự nhiên và hấp dẫn hơn.
    Tone: {req.tone}
    Caption:
    {req.caption}
    """

    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {"data": res.text}


@app.post("/ai/chatbot/qa")
def ask_chat(req: QuestionRequest):
    return answer_question(req.question)
