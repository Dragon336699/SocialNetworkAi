import uuid
from uuid import UUID
import pyodbc
from cassandra.cluster import Cluster
from datetime import datetime, timezone
from math import exp
from collections import defaultdict
from Database.database_cassandra import get_cassandra_session

from cassandra.query import BatchStatement

session = get_cassandra_session()

ACTION_WEIGHT = {
    'view': 1,
    'like': 2,
    'comment': 3
}

LAMBDA = 0.01

def time_decay(created_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    # Nếu created_at là naive, assume UTC
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    hours = (now - created_at).total_seconds() / 3600
    return exp(-LAMBDA * hours)

def find_user_similar (user_id: UUID):
    similar_users = defaultdict(float)

    query_posts = """
    SELECT post_id FROM user_post_interaction WHERE user_id = %s LIMIT 10;
    """

    posts = session.execute(query_posts, (user_id,))

    for row in posts:
        post_id = row.post_id

        query_users = """
            SELECT user_id, action, created_at FROM post_user_interaction WHERE post_id = %s LIMIT 10
        """

        users = session.execute(query_users, (post_id,))

        for u in users:
            if u.user_id == user_id:
                continue
            if u.user_id not in similar_users:
                weight = ACTION_WEIGHT.get(u.action, 1)
                decay = time_decay(u.created_at)
                similar_users[u.user_id] += weight * decay
            if len(similar_users) >= 20:
                return similar_users
    return similar_users

def get_post_viewed_user (user_id: UUID):
    query_posts = """
        SELECT post_id FROM user_post_interaction WHERE user_id = %s LIMIT 20;
    """

    posts = session.execute(query_posts, (user_id,))

    return posts

def feed_for_user (posts: list, user_id: UUID):
    if not posts:
        return

    insert_query = session.prepare("""
            INSERT INTO user_feed_unseen (user_id, created_at, post_id)
            VALUES (?, ?, ?)
        """)

    batch = BatchStatement()
    created_at = datetime.now(timezone.utc)

    for post in posts:
        seen_query = session.prepare("""
                    SELECT post_id FROM user_feed_seen
                    WHERE user_id = ? AND post_id = ?
                """)
        row = session.execute(seen_query, (user_id, post.post_id)).one()
        if row is None:
            # Chỉ insert nếu chưa seen
            print("Insert complete")
            batch.add(insert_query, (user_id, created_at, post.post_id))
    if batch:
        session.execute(batch)

