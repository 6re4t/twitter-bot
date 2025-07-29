import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import tweepy
from model import generate_reply

load_dotenv(dotenv_path="path of your api.env file")
TWITTER_API_KEY       = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET    = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN  = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER        = os.getenv("TWITTER_BEARER_TOKEN")
BOT_HANDLE            = os.getenv("TWITTER_HANDLE")

tweet_client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_SECRET,
    bearer_token=TWITTER_BEARER,
    wait_on_rate_limit=True
)

me     = tweet_client.get_user(username=BOT_HANDLE)
bot_id = me.data.id
print(f"Bot ID: {bot_id}", flush=True)

since_dt  = datetime.now(timezone.utc) - timedelta(hours=1)
since_str = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
print(f"Fetching mentions since {since_str} …", flush=True)

resp = tweet_client.search_recent_tweets(
    query=f"@{BOT_HANDLE} -is:retweet",
    start_time=since_str,
    tweet_fields=["author_id","created_at"],
    max_results=100
)
mentions = resp.data or []
print(f"Found {len(mentions)} mentions in past 24 h", flush=True)

since_id = None
for t in sorted(mentions, key=lambda x: x.created_at):
    if t.author_id == bot_id:
        continue
    since_id = max(since_id or t.id, t.id)
    reply = generate_reply(t.text)
    tweet_client.create_tweet(
        text=reply,
        in_reply_to_tweet_id=t.id
    )
    print(f"Replied to {t.id} ({t.created_at}): {reply}", flush=True)

class MentionStreamer(tweepy.StreamingClient):
    def __init__(self, bearer, reply_client, bot_id):
        super().__init__(bearer_token=bearer)
        self.reply_client = reply_client
        self.bot_id       = bot_id

    def on_tweet(self, tweet):
        if str(tweet.author_id) == str(self.bot_id):
            return
        reply = generate_reply(tweet.text)
        self.reply_client.create_tweet(
            text=reply,
            in_reply_to_tweet_id=tweet.id
        )
        print(f"Replied to {tweet.id}: {reply}", flush=True)

streamer = MentionStreamer(TWITTER_BEARER, tweet_client, bot_id)

existing = streamer.get_rules().data or []
if existing:
    streamer.delete_rules(ids=[r.id for r in existing])

streamer.add_rules(tweepy.StreamRule(f"@{BOT_HANDLE}"))
print("Listening for new mentions…", flush=True)
streamer.filter(tweet_fields=["author_id"])
