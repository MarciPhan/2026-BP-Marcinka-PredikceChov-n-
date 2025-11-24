import aiohttp
import asyncio
from datetime import datetime
import html
import time

RATE_LIMIT = 1.0
SLEEP_AFTER_429 = 10


class DiscourseCollector:
    def __init__(self, url, api_key, api_user, redis):
        self.base = url
        self.key = api_key
        self.user = api_user
        self.redis = redis

        checkpoint = self.redis.get_checkpoint("discourse")
        self.last_post_id = int(checkpoint) if checkpoint else 0
        
        self._last_request = 0
        self.history_fetched = False

    async def _safe_request(self, session, endpoint):
        url = f"{self.base}{endpoint}"

        delta = time.time() - self._last_request
        if delta < RATE_LIMIT:
            await asyncio.sleep(RATE_LIMIT - delta)

        self._last_request = time.time()

        try:
            async with session.get(url, headers={
                "Api-Key": self.key,
                "Api-Username": self.user
            }) as r:

                if r.status == 429:
                    print(f"⌛ [DISCOURSE] 429 Too Many Requests → čekám {SLEEP_AFTER_429}s")
                    await asyncio.sleep(SLEEP_AFTER_429)
                    return None

                if r.status != 200:
                    print(f"❌ [DISCOURSE] HTTP {r.status}: {url}")
                    return None

                return await r.json()

        except Exception as e:
            print(f"❌ [DISCOURSE] Request error: {e}")
            return None

    async def fetch_new_posts(self):
        """Fetch new posts (LIVE mode)"""
        async with aiohttp.ClientSession() as session:
            topics = await self._safe_request(session, "/latest.json")
            if not topics:
                return

            new_posts = 0

            for t in topics["topic_list"]["topics"]:
                tid = t["id"]

                data = await self._safe_request(session, f"/t/{tid}.json")
                if not data:
                    continue

                for post in data["post_stream"]["posts"]:
                    pid = post["id"]
                    if pid <= self.last_post_id:
                        continue

                    new_posts += 1
                    self.last_post_id = max(self.last_post_id, pid)

                    author_id = str(post.get("user_id", "0"))
                    content_raw = html.unescape(post.get("cooked", ""))
                    content_text = content_raw.replace("<p>", "").replace("</p>", "").strip()

                    created_at = datetime.fromisoformat(
                        post.get("created_at", "").replace("Z", "+00:00")
                    )

                    print(f"🟢 LIVE Discourse post: topic-{tid}: {content_text[:50]}")

                    # Save as LIVE message
                    self.redis.add_message(
                        source="discourse",
                        source_id=str(pid),
                        author_id=author_id,
                        content=content_text,
                        channel=f"topic-{tid}",
                        attachments=0,
                        replies=0,
                        reactions=0,
                        is_historical=False,  # ✅ LIVE MESSAGE
                        original_timestamp=created_at,
                    )

                    # Publish live update
                    self.redis.publish_realtime_message("messages", {
                        "type": "live_message",
                        "source": "discourse",
                        "author": f"user-{author_id}",
                        "topic": t.get("title", "Unknown"),
                        "content": content_text[:100],
                        "timestamp": post.get("created_at", ""),
                        "is_live": True,  # ✅ MARK AS LIVE
                        "is_historical": False
                    })

            if new_posts > 0:
                self.redis.set_checkpoint("discourse", str(self.last_post_id))
                print(f"🔥 [DISCOURSE] Nových postů: {new_posts}")

    async def fetch_full_history(self):
        """Fetch complete history (HISTORICAL mode)"""
        if self.last_post_id > 0:
            print(f"✅ [DISCOURSE] Historie již načtena (checkpoint {self.last_post_id})")
            self.history_fetched = True

            self.redis.publish_realtime_message("messages", {
                "type": "history_complete",
                "source": "discourse",
                "message": "Historie Discourse načtena z checkpointu",
                "is_historical": True
            })
            return

        print("⏳ [DISCOURSE] Stahuji KOMPLETNÍ historii všech postů…")

        self.redis.publish_realtime_message("messages", {
            "type": "history_start",
            "source": "discourse",
            "message": "⏳ Načítám KOMPLETNÍ historii Discourse...",
            "is_historical": True
        })

        async with aiohttp.ClientSession() as session:
            all_posts = []
            before_post_id = None
            total_posts = 0

            while True:
                endpoint = "/posts.json" if not before_post_id else f"/posts.json?before={before_post_id}"
                data = await self._safe_request(session, endpoint)
                if not data:
                    break

                posts = data.get("latest_posts", [])
                if not posts:
                    break

                all_posts.extend(posts)
                total_posts += len(posts)

                before_post_id = posts[-1]["id"]

                print(f"📦 [DISCOURSE] Načteno {total_posts} postů...")

                if total_posts % 500 == 0:
                    self.redis.publish_realtime_message("messages", {
                        "type": "history_progress",
                        "source": "discourse",
                        "count": total_posts,
                        "message": f"Načítám Discourse: {total_posts} postů...",
                        "is_historical": True
                    })

                if len(posts) < 20:
                    break

            print(f"🎯 [DISCOURSE] Celkem načteno {len(all_posts)} postů")

            topics_set = set()

            for i, post in enumerate(all_posts):
                pid = post["id"]
                self.last_post_id = max(self.last_post_id, pid)

                author_id = str(post.get("user_id", "0"))
                topic_id = post.get("topic_id", 0)
                topics_set.add(topic_id)

                content_raw = html.unescape(post.get("cooked", ""))
                content_text = content_raw.replace("<p>", "").replace("</p>", "").strip()

                created_at = datetime.fromisoformat(
                    post.get("created_at", "").replace("Z", "+00:00")
                )

                # Save as HISTORICAL message
                self.redis.add_message(
                    source="discourse",
                    source_id=str(pid),
                    author_id=author_id,
                    content=content_text,
                    channel=f"topic-{topic_id}",
                    attachments=0,
                    replies=0,
                    reactions=0,
                    is_historical=True,  # ✅ HISTORICAL MESSAGE
                    original_timestamp=created_at
                )

                if (i + 1) % 1000 == 0:
                    self.redis.publish_realtime_message("messages", {
                        "type": "history_progress",
                        "source": "discourse",
                        "count": i + 1,
                        "topics": len(topics_set),
                        "message": f"Zpracováno {i + 1} postů...",
                        "is_historical": True
                    })

        self.redis.set_checkpoint("discourse", str(self.last_post_id))
        self.history_fetched = True

        total_topics = len(topics_set)

        self.redis.publish_realtime_message("messages", {
            "type": "history_complete",
            "source": "discourse",
            "count": len(all_posts),
            "topics": total_topics,
            "message": f"✅ Discourse historie hotova: {len(all_posts)} postů z {total_topics} témat",
            "is_historical": True
        })

        print(f"🎉 [DISCOURSE] KOMPLETNÍ historie: {len(all_posts)} postů")

    async def listen_realtime(self):
        """Poll for new posts every 30 seconds"""
        print("🔄 [DISCOURSE REALTIME] Polling každých 30s")
        
        while True:
            await asyncio.sleep(30)
            
            if self.history_fetched:
                try:
                    await self.fetch_new_posts()
                except Exception as e:
                    print(f"❌ [DISCOURSE] Error in realtime polling: {e}")
            else:
                print("⏸️ Waiting for history to complete...")

    async def run(self):
        await self.fetch_full_history()
        await self.listen_realtime()