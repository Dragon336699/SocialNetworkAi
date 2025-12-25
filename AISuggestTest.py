import joblib
import pandas as pd

model = joblib.load("friend_recommend_model.pkl")

input_data = pd.DataFrame([{
    "view_count": 6,
    "search_count":1,
    "like_count": 1,
    "last_days": 5
}])

prob = model.predict_proba(input_data)[0][1]
print("Probability of becoming friends:", prob)