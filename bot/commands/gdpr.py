import discord
from discord.ext import commands
from discord import app_commands
import redis.asyncio as redis
import os
import json
from datetime import datetime
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class GDPRCommands(commands.Cog):
    # Příkazy pro správu dat uživatelů (GDPR)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
        self.r = redis.Redis(connection_pool=self.pool)

    async def cog_unload(self):
        await self.pool.disconnect()

    @app_commands.command(name="privacy", description="Zobrazí informace o ochraně osobních údajů a GDPR")
    async def privacy(self, interaction: discord.Interaction):
        # Zobrazí info o tom, co se o lidech sbírá
        embed = discord.Embed(
            title="Ochrana osobních údajů - Metricord",
            description="Informace o tom, jaká data sbíráme a jak je chráníme.",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Co sbíráme",
            value=(
                "• **Metadata zpráv:** Počet zpráv, délka textu, zda je odpověď\n"
                "• **Voice aktivita:** Délka času ve voice kanálech\n"
                "• **Moderační akce:** Bany, kicky, timeouty (pouze pro moderátory)\n"
                "• **Uživatelské info:** Discord jméno, avatar, role\n"
                "• **Discord User ID:** Pro identifikaci uživatele"
            ),
            inline=False
        )

        embed.add_field(
            name="Co nesbíráme",
            value=(
                "• **Obsah zpráv** - nikdy neukládáme text zpráv\n"
                "• **Soukromé konverzace (DM)**\n"
                "• **Hlasové nahrávky**"
            ),
            inline=False
        )

        embed.add_field(
            name="Proč sbíráme data",
            value=(
                "• Analýza a statistiky serveru\n"
                "• Sledování aktivity moderátorů\n"
                "• Žebříčky a metriky zapojení\n"
                "• Predikce pro bakalářskou práci"
            ),
            inline=False
        )

        embed.add_field(
            name="Jak dlouho ukládáme",
            value=(
                "• **Uživatelské info:** 7 dní (automaticky expiruje)\n"
                "• **Event data:** Neomezené (až do smazání)\n"
                "• **Statistiky:** Neomezené (až do smazání)"
            ),
            inline=False
        )

        embed.add_field(
            name="Tvoje práva (GDPR)",
            value=(
                "• **`/gdpr export`** - Stáhnout kopii všech tvých dat\n"
                "• **`/gdpr delete`** - Smazat všechna tvá data z databáze\n"
                "• **`/privacy`** - Zobrazit tuto zprávu"
            ),
            inline=False
        )

        embed.add_field(
            name="Zabezpečení",
            value=(
                "• Data jsou uložena v zabezpečené Redis databázi\n"
                "• Přístup pouze pro autorizované procesy\n"
                "• Žádná data nejsou sdílena s třetími stranami"
            ),
            inline=False
        )

        embed.set_footer(text="Metricord • GDPR Compliant")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    gdpr_group = app_commands.Group(name="gdpr", description="Správa osobních údajů podle GDPR")

    @gdpr_group.command(name="export", description="Exportovat všechna tvá data uložená v databázi")
    async def gdpr_export(self, interaction: discord.Interaction):
        """Export all user data stored in Redis."""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        try:
            # Collect all data
            data_summary = {
                "user_info": {},
                "guilds": {}
            }
            
            # 1. User info
            user_info_key = f"user:info:{user_id}"
            user_info = await self.r.hgetall(user_info_key)
            if user_info:
                data_summary["user_info"] = user_info
            
            # 2. Get all guilds the bot is in
            guild_ids = await self.r.smembers("bot:guilds")
            
            # 3. Collect events per guild
            for guild_id in guild_ids:
                guild_data = {
                    "messages": 0,
                    "voice_sessions": 0,
                    "voice_duration": 0,
                    "actions": 0
                }
                
                # Messages
                msg_key = f"events:msg:{guild_id}:{user_id}"
                msg_count = await self.r.zcard(msg_key)
                guild_data["messages"] = msg_count
                
                # Voice
                voice_key = f"events:voice:{guild_id}:{user_id}"
                voice_events = await self.r.zrange(voice_key, 0, -1)
                guild_data["voice_sessions"] = len(voice_events)
                
                total_duration = 0
                for evt_json in voice_events:
                    try:
                        evt = json.loads(evt_json)
                        total_duration += evt.get("duration", 0)
                    except:
                        pass
                guild_data["voice_duration"] = total_duration
                
                # Actions
                action_key = f"events:action:{guild_id}:{user_id}"
                action_count = await self.r.zcard(action_key)
                guild_data["actions"] = action_count
                
                # Only include guilds with data
                if any([msg_count, len(voice_events), action_count]):
                    data_summary["guilds"][guild_id] = guild_data
            
            # Format output
            embed = discord.Embed(
                title="Tvoje data v Metricord",
                description="Export všech dat uložených v databázi",
                color=discord.Color.green()
            )
            
            # User info
            if data_summary["user_info"]:
                info = data_summary["user_info"]
                user_text = f"**Jméno:** {info.get('name', 'N/A')}\n"
                user_text += f"**Avatar:** [Link]({info.get('avatar', 'N/A')})\n"
                roles = info.get('roles', '')
                if roles:
                    user_text += f"**Role IDs:** {roles[:100]}..."
                embed.add_field(name="Uživatelské info", value=user_text, inline=False)
            
            # Guild data
            if data_summary["guilds"]:
                for gid, gdata in data_summary["guilds"].items():
                    guild_name = f"Server {gid}"
                    try:
                        guild = self.bot.get_guild(int(gid))
                        if guild:
                            guild_name = guild.name
                    except:
                        pass
                    
                    guild_text = f"**📨 Zpráv:** {gdata['messages']}\n"
                    guild_text += f"**🎙️ Voice sessions:** {gdata['voice_sessions']}\n"
                    
                    if gdata['voice_duration'] > 0:
                        hours = gdata['voice_duration'] / 3600
                        guild_text += f"**⏱️ Voice čas:** {hours:.1f}h\n"
                    
                    if gdata['actions'] > 0:
                        guild_text += f"**⚖️ Moderační akce:** {gdata['actions']}\n"
                    
                    embed.add_field(name=f"{guild_name}", value=guild_text, inline=False)
            else:
                embed.add_field(
                    name="Žádná data",
                    value="V databázi o tobě nic nemáme.",
                    inline=False
                )
            
            embed.set_footer(text=f"Export vygenerován: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"GDPR export error: {e}")
            await interaction.followup.send(
                "❌ Chyba při exportu dat. Kontaktuj administrátora.",
                ephemeral=True
            )

    @gdpr_group.command(name="delete", description="Smazat všechna tvá data z databáze (NEVRATNÉ!)")
    async def gdpr_delete(self, interaction: discord.Interaction):
        """Delete all user data from Redis."""
        user_id = str(interaction.user.id)
        
        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self, parent_cog, user_id):
                super().__init__(timeout=60.0)
                self.parent_cog = parent_cog
                self.user_id = user_id
                self.value = None
            
            @discord.ui.button(label="Ano, smazat data", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                
                try:
                    deleted_keys = []
                    
                    # 1. Delete user info
                    key = f"user:info:{self.user_id}"
                    if await self.parent_cog.r.exists(key):
                        await self.parent_cog.r.delete(key)
                        deleted_keys.append(key)
                    
                    # 2. Get all guilds
                    guild_ids = await self.parent_cog.r.smembers("bot:guilds")
                    
                    # 3. Delete events per guild
                    for guild_id in guild_ids:
                        # Messages
                        key = f"events:msg:{guild_id}:{self.user_id}"
                        if await self.parent_cog.r.exists(key):
                            await self.parent_cog.r.delete(key)
                            deleted_keys.append(key)
                        
                        # Voice
                        key = f"events:voice:{guild_id}:{self.user_id}"
                        if await self.parent_cog.r.exists(key):
                            await self.parent_cog.r.delete(key)
                            deleted_keys.append(key)
                        
                        # Actions
                        key = f"events:action:{guild_id}:{self.user_id}"
                        if await self.parent_cog.r.exists(key):
                            await self.parent_cog.r.delete(key)
                            deleted_keys.append(key)
                        
                        # Activity states
                        for state_key in ["chat_start", "chat_last", "voice_start"]:
                            key = f"activity:state:{guild_id}:{self.user_id}:{state_key}"
                            if await self.parent_cog.r.exists(key):
                                await self.parent_cog.r.delete(key)
                                deleted_keys.append(key)
                    
                    # 4. Delete daily stats (scan pattern)
                    async for key in self.parent_cog.r.scan_iter(f"stats:day:*:*:{self.user_id}"):
                        await self.parent_cog.r.delete(key)
                        deleted_keys.append(key)
                    
                    # Log deletion
                    log_key = f"gdpr:deletion_log:{self.user_id}"
                    await self.parent_cog.r.set(
                        log_key,
                        json.dumps({
                            "timestamp": datetime.now().isoformat(),
                            "deleted_keys_count": len(deleted_keys)
                        }),
                        ex=86400 * 30  # Keep log for 30 days
                    )
                    
                    embed = discord.Embed(
                        title="Všechno smazáno",
                        description=(
                            f"Tvoje data byla smazána z databáze.\n\n"
                            f"**Počet smazaných klíčů:** {len(deleted_keys)}\n"
                            f"**Čas:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"Pokud budeš zase psát, bot začne sbírat data nanovo."
                        ),
                        color=discord.Color.green()
                    )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                    # Disable buttons
                    for item in self.children:
                        item.disabled = True
                    await interaction.message.edit(view=self)
                    
                except Exception as e:
                    print(f"GDPR delete error: {e}")
                    await interaction.followup.send(
                        "❌ Chyba při mazání dat. Kontaktuj administrátora.",
                        ephemeral=True
                    )
            
            @discord.ui.button(label="❌ Ne, zrušit", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                
                embed = discord.Embed(
                    title="❌ Zrušeno",
                    description="Žádná data nebyla smazána.",
                    color=discord.Color.orange()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                await interaction.message.edit(view=self)
        
        # Send confirmation message
        embed = discord.Embed(
            title="⚠️ Smazání dat - Potvrzení",
            description=(
                "**VAROVÁNÍ:** Tato akce je NEVRATNÁ!\n\n"
                "Budou smazána všechna data včetně:\n"
                "• Uživatelského profilu\n"
                "• Historie zpráv (metadata)\n"
                "• Voice aktivita\n"
                "• Moderační akce\n"
                "• Všechny statistiky\n\n"
                "Opravdu chceš pokračovat?"
            ),
            color=discord.Color.red()
        )
        
        view = ConfirmView(self, user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GDPRCommands(bot))
