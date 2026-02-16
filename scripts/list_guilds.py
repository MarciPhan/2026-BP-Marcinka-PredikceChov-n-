import discord
import os
import asyncio

TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True

class GuildLister(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print("Guilds:")
        for guild in self.guilds:
            print(f"- {guild.name} ({guild.id})")
        await self.close()

client = GuildLister(intents=intents)
client.run(TOKEN)
