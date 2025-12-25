from flask import Flask, request, jsonify
from uuid import UUID
import joblib
import pandas as pd
from datetime import datetime
from cassandra.cluster import Cluster

app = Flask(__name__)

model = joblib.load("friend_recommend_model.pkl")

cluster = Cluster(["127.0.0.1"])
session = cluster.connect("fricon")

def get_user_interaction(user_id):
    counter = """
    SELECT target_user_id, view_count, like_count, search_count
    FROM user_interaction_counter WHERE user_id = %s
    """
    meta = """
    SELECT target_user_id, last_interaction FROM user_interaction_meta WHERE user_id = %s
    """

    counter_rows = session.execute(counter, (user_id,))
    meta_rows = session.execute(meta, (user_id,))

    meta_map = {r.target_user_id: r.last_interaction for r in meta_rows}

    now = datetime.utcnow()
    data = []

    for r in counter_rows:
        last = meta_map.get(r.target_user_id)
        last_days = (now - last.replace(tzinfo=None)).days if last else 999

        data.append({
            "target_user_id": str(r.target_user_id),
            "view_count": int(r.view_count or 0),
            "like_count": int(r.like_count or 0),
            "search_count": int(r.search_count or 0),
            "last_days": last_days
        })

    return pd.DataFrame(data)

@app.route("/friend/recommend")
def recommend():
    try:
        user_id = UUID(request.args.get("user_id"))
        df = get_user_interaction(user_id)

        if df.empty:
            return jsonify([])

        X = df[["view_count", "like_count", "search_count", "last_days"]]
        probs = model.predict_proba(X)[:, 1]

        df["probs"] = probs
        result = df.sort_values("probs", ascending=False).head(10)

        return jsonify(result[["target_user_id", "probs"]].to_dict("records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
