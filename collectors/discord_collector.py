import asyncio
import discord
import datetime
import traceback


class DiscordCollector(discord.Client):
    def __init__(self, token, redis, intents):
        super().__init__(intents=intents)

        self.token = token
        self.redis = redis

        self.history_in_progress = False
        self.history_fetched = False
        self.last_message_id = 0

    # ==========================================================
    # STATIC → backend calls this
    # ==========================================================
    @staticmethod
    def create_intents():
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        return intents

    # ==========================================================
    # ENTRYPOINT → backend calls this
    # ==========================================================
    async def run_collector(self):
        await self.start(self.token)

    # ==========================================================
    # READY → start history fetch
    # ==========================================================
    async def on_ready(self):
        print(f"🟢 Logged in as {self.user}")
        asyncio.create_task(self.fetch_full_history())

    # ==========================================================
    # FULL HISTORY
    # ==========================================================
    async def fetch_full_history(self):
        self.history_in_progress = True
        print("📚 Fetching full Discord history...")

        try:
            for guild in self.guilds:
                print(f"🔍 Guild: {guild.name}")

                for channel in guild.text_channels:
                    print(f"📨 #{channel.name}: fetching messages")

                    async for msg in channel.history(limit=None, oldest_first=True):
                        mid = int(msg.id)
                        self.last_message_id = max(self.last_message_id, mid)

                        self.redis.add_message(
                            source="discord",
                            source_id=str(msg.id),
                            author_id=str(msg.author.id),
                            content=msg.content or "",
                            channel=channel.name,
                            attachments=len(msg.attachments),
                            replies=0,
                            reactions=len(msg.reactions),
                            is_historical=True,
                            original_timestamp=msg.created_at
                        )
        except Exception:
            traceback.print_exc()
        finally:
            print("📚 Full history DONE.")
            self.history_in_progress = False
            self.history_fetched = True

    # ==========================================================
    # REALTIME MESSAGES
    # ==========================================================
    async def on_message(self, message):
        if message.author.bot:
            return

        mid = int(message.id)

        # během historií pouštíme ONLY live zprávy (ID > last_message_id)
        if self.history_in_progress:
            if mid <= self.last_message_id:
                return

        # prevence duplicit při race condition
        if not self.history_fetched and mid <= self.last_message_id:
            return

        # store live message
        self.redis.add_message(
            source="discord",
            source_id=str(message.id),
            author_id=str(message.author.id),
            content=message.content or "",
            channel=message.channel.name,
            attachments=len(message.attachments),
            replies=0,
            reactions=len(message.reactions),
            is_historical=False,
            original_timestamp=message.created_at
        )

        # realtime publish
        self.redis.publish_realtime_message("messages", {
            "type": "live_message",
            "source": "discord",
            "channel": message.channel.name,
            "author": str(message.author),
            "content": message.content[:100] if message.content else "",
            "timestamp": str(message.created_at),
            "is_live": True,
            "is_historical": False
        })

        print(f"⚡ LIVE #{message.channel.name}: {message.content[:40]}")
