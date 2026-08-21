
import discord
from discord.ext import commands
from discord import app_commands
import redis.asyncio as redis
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os

from shared.models import CommunityModels
from shared.redis_client import get_redis_client

class HealthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="health", description="Zobrazí celkové zdraví komunity a pokročilé predikce.")
    @app_commands.describe(research="Zobrazit detailní Markovův model a analýzu přežití?")
    async def health(self, interaction: discord.Interaction, research: bool = False):
        await interaction.response.defer()
        
        guild = interaction.guild
        r = await get_redis_client()
        
        # 1. Základní metriky
        total_members = guild.member_count
        
        # Získáme DAU z HLL (z stats_hll.py)
        today_str = datetime.now().strftime("%Y%m%d")
        dau = await r.pfcount(f"hll:dau:{guild.id}:{today_str}")
        
        # Activity Rate
        activity_rate = (dau / total_members) if total_members > 0 else 0
        
        # Toxicity Index (posledních 7 dní)
        # Sčítáme akce z redis
        total_actions = 0
        async for key in r.scan_iter(f"events:action:{guild.id}:*"):
            # V reálném nasazení bychom filtrovali časem přímo v redis (zrangebyscore)
            # Tady pro jednoduchost vezmeme celkový počet zpráv vs akcí
            actions = await r.zcard(key)
            total_actions += actions
            
        total_msgs_str = await r.get(f"stats:total_msgs:{guild.id}")
        total_msgs = int(total_msgs_str) if total_msgs_str else 1
        mii = (total_actions / total_msgs)
        
        # Doporučený počet moderátorů
        # N = (DAU * (1 + MII * 10)) / 150 + 2
        rec_mods = int(np.ceil((dau * (1 + mii * 10)) / 150 + 2))
        
        embed = discord.Embed(
            title=f"📊 Health Report: {guild.name}",
            color=discord.Color.green() if mii < 0.01 else discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👥 Aktivita (AER)", value=f"**{activity_rate:.1%}** (DAU: {dau})", inline=True)
        embed.add_field(name="⚠️ Moderační zátěž (MII)", value=f"**{mii:.2%}**", inline=True)
        embed.add_field(name="🛡️ Doporučený tým", value=f"**{rec_mods} moderátorů**", inline=True)
        
        status_text = "✅ Komunita je zdravá a stabilní."
        if activity_rate < 0.05: status_text = "💤 Server vykazuje nízkou aktivitu (pod 5 %)."
        if mii > 0.02: status_text = "🚨 Vysoká moderační zátěž! Tým je pravděpodobně přetížen."
        
        embed.description = status_text
        
        if research:
            from web.backend.utils import get_health_research_data
            
            # Zavoláme reálnou ML pipeline z backendu
            research_data = await get_health_research_data(guild.id)
            
            if research_data.get("success"):
                p_stay_active = research_data.get("retention_pct", 0) / 100.0
                p_churn = research_data.get("churn_risk_pct", 0) / 100.0
                life_exp = research_data.get("life_expectancy_days", 0)
                median_survival = research_data.get("median_survival_days", 0)
                
                res_text = (
                    f"**Markovova analýza (Predikce 7 dní):**\n"
                    f"- Pravděpodobnost setrvání (Retention): **{p_stay_active:.1%}**\n"
                    f"- Riziko odchodu (Churn Risk): **{p_churn:.1%}**\n\n"
                    f"**Analýza přežití (Survival):**\n"
                    f"- Očekávaná délka aktivity: **{life_exp} dní**\n"
                    f"- Medián přežití aktivity: **{median_survival} dní**"
                )
            else:
                res_text = "Nepodařilo se vypočítat výzkumná data (nedostatek historie nebo chyba zpracování)."
                
            embed.add_field(name="🧪 Výzkumná data (Markov/Survival)", value=res_text, inline=False)
            
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HealthCog(bot))
