import random
import pandas as pd

random.seed(42)

data = []

NUM_SAMPLES = 2000

for _ in range(NUM_SAMPLES):
    view = random.randint(0, 8)
    search = random.randint(0, 10)
    like = random.randint(0, 5)
    last_days = random.randint(0, 30)

    # Logic sinh label (chỉ để tạo data)
    score = (
        view * 0.12 +
        search * 0.25 +
        like * 0.15 -
        last_days * 0.1
    )

    probability = 1 / (1 + pow(2.718, -score))
    label = 1 if random.random() < probability else 0

    data.append([
        view,
        search,
        like,
        last_days,
        label
    ])

df = pd.DataFrame(data, columns=[
    "view_count",
    "search_count",
    "like_count",
    "last_days",
    "label"
])

df.to_csv("interaction_dataset.csv", index=False)

print("Synthetic dataset generated:", len(df))
