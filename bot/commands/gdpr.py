import discord
from discord.ext import commands
from discord import app_commands
import redis.asyncio as redis
import os
import json
from datetime import datetime

from shared.config import settings
from shared.community_health import keys as health_keys

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
            title="Ochrana osobních údajů - CommunityMetrics",
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
                f"• **Uživatelské info:** 7 dní (automaticky expiruje)\n"
                f"• **Event data:** {settings.event_retention_days} dní (poté automaticky mazáno), agregace a indexy déle\n"
                f"• **Statistiky:** HyperLogLog a hodinové agregace nezávisle na retenci eventů"
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

        embed.set_footer(text="CommunityMetrics • GDPR Compliant")

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
                    "actions": 0,
                    "health_messages": 0,
                    "help_requests": 0,
                    "mod_events": 0,
                    "leaderboard_voice_seconds": 0,
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

                # Community health data (used by the /health prediction command)
                guild_data["health_messages"] = await self.r.zcard(health_keys.user_messages(guild_id, user_id))
                guild_data["help_requests"] = await self.r.zcard(health_keys.help_user(guild_id, user_id))
                mod_ids = set(await self.r.zrange(health_keys.mod_events_moderator(guild_id, user_id), 0, -1))
                mod_ids |= set(await self.r.zrange(health_keys.mod_events_target(guild_id, user_id), 0, -1))
                guild_data["mod_events"] = len(mod_ids)

                voice_seconds = await self.r.zscore(f"stats:voice_duration:{guild_id}", user_id)
                guild_data["leaderboard_voice_seconds"] = int(voice_seconds or 0)

                # Only include guilds with data
                if any([msg_count, len(voice_events), action_count, guild_data["health_messages"],
                        guild_data["help_requests"], guild_data["mod_events"], voice_seconds]):
                    data_summary["guilds"][guild_id] = guild_data

            # Format output
            embed = discord.Embed(
                title="Tvoje data v CommunityMetrics",
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

                    if gdata['health_messages'] > 0:
                        guild_text += f"**💬 Zprávy (community health):** {gdata['health_messages']}\n"

                    if gdata['help_requests'] > 0:
                        guild_text += f"**🆘 Help požadavky:** {gdata['help_requests']}\n"

                    if gdata['mod_events'] > 0:
                        guild_text += f"**🛡️ Moderační eventy (health):** {gdata['mod_events']}\n"

                    if gdata['leaderboard_voice_seconds'] > 0:
                        hours = gdata['leaderboard_voice_seconds'] / 3600
                        guild_text += f"**🎧 Voice (leaderboard):** {hours:.1f}h\n"

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
                    r = self.parent_cog.r
                    uid = self.user_id

                    # 3. Delete events per guild
                    for guild_id in guild_ids:
                        # Messages
                        key = f"events:msg:{guild_id}:{uid}"
                        if await r.exists(key):
                            await r.delete(key)
                            deleted_keys.append(key)

                        # Voice
                        key = f"events:voice:{guild_id}:{uid}"
                        if await r.exists(key):
                            await r.delete(key)
                            deleted_keys.append(key)

                        # Actions
                        key = f"events:action:{guild_id}:{uid}"
                        if await r.exists(key):
                            await r.delete(key)
                            deleted_keys.append(key)

                        # Activity states
                        for state_key in ["chat_start", "chat_last", "voice_start"]:
                            key = f"activity:state:{guild_id}:{uid}:{state_key}"
                            if await r.exists(key):
                                await r.delete(key)
                                deleted_keys.append(key)

                        # Community health: messages authored by the user
                        msg_ids = await r.zrange(health_keys.user_messages(guild_id, uid), 0, -1)
                        for mid in msg_ids:
                            await r.delete(health_keys.message(guild_id, mid))
                            await r.zrem(health_keys.messages_index(guild_id), mid)
                        if msg_ids:
                            deleted_keys.append(f"health:message:{guild_id}:*")
                        key = health_keys.user_messages(guild_id, uid)
                        if await r.exists(key):
                            await r.delete(key)
                            deleted_keys.append(key)

                        # Community health: help requests opened by the user
                        help_ids = await r.zrange(health_keys.help_user(guild_id, uid), 0, -1)
                        for hid in help_ids:
                            await r.delete(health_keys.help_item(guild_id, hid))
                            await r.zrem(health_keys.help_all(guild_id), hid)
                            await r.zrem(health_keys.help_open(guild_id), hid)
                            await r.zrem(health_keys.help_answered(guild_id), hid)
                        if help_ids:
                            deleted_keys.append(f"health:help:{guild_id}:*")
                        key = health_keys.help_user(guild_id, uid)
                        if await r.exists(key):
                            await r.delete(key)
                            deleted_keys.append(key)

                        # Community health: moderation events (as moderator and as target)
                        mod_ids = set(await r.zrange(health_keys.mod_events_moderator(guild_id, uid), 0, -1))
                        mod_ids |= set(await r.zrange(health_keys.mod_events_target(guild_id, uid), 0, -1))
                        for eid in mod_ids:
                            event_data = await r.hgetall(health_keys.mod_event(guild_id, eid))
                            other_mod = event_data.get("moderator_id")
                            other_target = event_data.get("target_user_id")
                            await r.delete(health_keys.mod_event(guild_id, eid))
                            await r.zrem(health_keys.mod_events(guild_id), eid)
                            # Also remove from the other party's index, so a
                            # single-sided deletion request doesn't leave a
                            # dangling event id in their moderator/target set.
                            if other_mod:
                                await r.zrem(health_keys.mod_events_moderator(guild_id, other_mod), eid)
                            if other_target:
                                await r.zrem(health_keys.mod_events_target(guild_id, other_target), eid)
                        if mod_ids:
                            deleted_keys.append(f"health:mod_event:{guild_id}:*")
                        for key in [
                            health_keys.mod_events_moderator(guild_id, uid),
                            health_keys.mod_events_target(guild_id, uid),
                        ]:
                            if await r.exists(key):
                                await r.delete(key)
                                deleted_keys.append(key)
                        async for key in r.scan_iter(health_keys.mod_pair(guild_id, uid, "*")):
                            await r.delete(key)
                            deleted_keys.append(key)
                        async for key in r.scan_iter(health_keys.mod_pair(guild_id, "*", uid)):
                            await r.delete(key)
                            deleted_keys.append(key)

                        # Community health: departure records
                        departure_ids = []
                        async for key in r.scan_iter(f"{health_keys.departure(guild_id, uid)}:*"):
                            departure_ids.append(key.split(":")[-1])
                            await r.delete(key)
                            deleted_keys.append(key)
                        for did in departure_ids:
                            await r.zrem(health_keys.departures(guild_id), f"{uid}:{did}")

                        # Community health: scheduled event interest/attendance
                        event_ids = await r.smembers(health_keys.events_index(guild_id))
                        for eid in event_ids:
                            for key in [
                                health_keys.event_interested(guild_id, eid),
                                health_keys.event_attended(guild_id, eid),
                            ]:
                                if await r.srem(key, uid):
                                    deleted_keys.append(key)

                        # Analytics: voice duration and message leaderboard
                        if await r.zscore(f"stats:voice_duration:{guild_id}", uid) is not None:
                            await r.zrem(f"stats:voice_duration:{guild_id}", uid)
                            deleted_keys.append(f"stats:voice_duration:{guild_id}")
                        if await r.zscore(f"leaderboard:messages:{guild_id}", uid) is not None:
                            await r.zrem(f"leaderboard:messages:{guild_id}", uid)
                            deleted_keys.append(f"leaderboard:messages:{guild_id}")
                        key = f"leaderboard:msg_lengths:{guild_id}:{uid}"
                        if await r.exists(key):
                            await r.delete(key)
                            deleted_keys.append(key)
                        async for key in r.scan_iter(f"stats:user_daily:{guild_id}:*"):
                            if await r.zscore(key, uid) is not None:
                                await r.zrem(key, uid)
                                deleted_keys.append(key)

                    # 4. Delete daily stats (scan pattern)
                    async for key in r.scan_iter(f"stats:day:*:*:{uid}"):
                        await r.delete(key)
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
