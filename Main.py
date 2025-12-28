import joblib
import pandas as pd
from datetime import datetime
from cassandra.cluster import Cluster
from fastapi import FastAPI
from uuid import UUID
import pyodbc
from google import genai
from dotenv import load_dotenv
import os

from Requests.CaptionRequest import CaptionRequest
from Requests.SummarizePostRequest import SummarizePostRequest

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

sql_conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LAPTOP-ROIBK9BH\\SQLEXPRESS;"
    "DATABASE=SocialNetwork;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

model = joblib.load("friend_recommend_model.pkl")

cluster = Cluster(["127.0.0.1"])
session = cluster.connect("fricon")

def get_friend_list(user_id):
    query = """
    SELECT RelatedUserId FROM UserRelation WHERE user_id = ?
    """
    cursor = sql_conn.cursor()
    rows = cursor.execute(query, str(user_id)).fetchall()
    return set(UUID(row[0]) for row in rows)

def get_user_interaction(user_id):
    counter = """
    SELECT target_user_id, view_count, search_count, like_count
    FROM user_interaction_counter WHERE user_id = %s
    """

    meta = """
    SELECT target_user_id, last_interaction FROM user_interaction_meta WHERE user_id = %s
    """
    
    try:
        counter_rows = list(session.execute(counter, (user_id,)))

        meta_rows = list(session.execute(meta, (user_id,)))

    except Exception as e:
        print(f"[ERROR] Exception during Cassandra query: {e}")
        raise

    meta_map = {
        r.target_user_id: r.last_interaction
        for r in meta_rows
    }

    now = datetime.utcnow()
    data = []
    
    if counter_rows:
        print("[DEBUG] First counter row:", counter_rows[0])

    for r in counter_rows:
        last_interaction = meta_map.get(r.target_user_id)
        print("Last interaction: ", last_interaction)
        if last_interaction:
            last_interaction = last_interaction.replace(tzinfo=None)
            last_days = (now - last_interaction).days
        else:
            last_days = 999

        data.append({
            "target_user_id": r.target_user_id,
            "view_count": r.view_count or 0,
            "search_count": r.search_count or 0,
            "like_count": r.like_count or 0,
            "last_days": last_days
        })

    df = pd.DataFrame(data)
    print("[DEBUG] Created DataFrame. Shape:", df.shape)
    if not df.empty:
        print("[DEBUG] DataFrame head:\n", df.head())
    return df

def recommend_friends(user_id, top_k=10, threshold=0.6):
    df = get_user_interaction(user_id)
    if df.empty:
        print("[DEBUG] DataFrame is empty. No recommendations.")
        return []

    friend_ids = get_friend_list(user_id)
    df = df[~df["target_user_id"].isin(friend_ids)]


    feature_cols = ["view_count", "search_count", "like_count", "last_days"]

    try:
        probs = model.predict_proba(df[feature_cols])[:, 1]
    except Exception as e:
        print(f"[ERROR] Exception during model prediction: {e}")
        raise

    df["probs"] = probs
    df["label"] = (df["probs"] >= threshold).astype(int)

    result = (
        df[df["label"] == 1]
        .sort_values("probs", ascending=False)
        .head(top_k)
    )

    return result[["target_user_id", "probs"]].to_dict(orient="records")


app = FastAPI()

@app.get("/friend/recommend")
def recommend(user_id: UUID):
    print("API END")
    data = recommend_friends(user_id)
    return {
        "user_id": user_id,
        "recommendations": data
    }

@app.post("/post/summary")
def summarize_post (req: SummarizePostRequest):
    prompts = f"""
        Bạn là trợ lý tóm tắt nội dung bài viết mạng xã hội.
        Tóm tắt nội dung sau trong 3–5 dòng, rõ ý, trung lập.
        Nội dung:
        {req.content}
    """

    response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = prompts
    )

    return {
        "data": response.text
    }

@app.post("/post/rewrite")
def summarize_post (req: CaptionRequest):
    prompts = f"""
        Bạn là trợ lý viết caption cho mạng xã hội.
        Viết lại caption sau cho tự nhiên, hấp dẫn hơn.
        Tone: {req.tone}
        Giữ nguyên ý, không thêm thông tin mới. Chỉ trả về nội dung mới, không hỏi lại người dùng hay đánh giá caption
        
        Caption: 
        {req.caption}
    """

    response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = prompts
    )

    return {
        "data": response.text
    }