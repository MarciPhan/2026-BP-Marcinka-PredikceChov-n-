
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
        
        from web.backend.utils import get_health_research_data
        research_data = await get_health_research_data(guild.id)
        
        # MII (Centralizovaný výpočet)
        mii_val = research_data.get("mii")
        rec_mods_calc = mii_val if mii_val is not None else 0.0
        
        # Doporučený počet moderátorů
        # N = (DAU * (1 + MII * 10)) / 150 + 2
        rec_mods = int(np.ceil((dau * (1 + rec_mods_calc * 10)) / 150 + 2))
        
        embed = discord.Embed(
            title=f"📊 Health Report: {guild.name}",
            color=discord.Color.green() if mii_val is None or mii_val < 0.01 else discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👥 Aktivita (AER)", value=f"**{activity_rate:.1%}** (DAU: {dau})", inline=True)
        mii_str = f"**{mii:.2%}**" if mii_val is not None else "**N/A**"
        embed.add_field(name="⚠️ Moderační zátěž (MII)", value=mii_str, inline=True)
        embed.add_field(name="🛡️ Doporučený tým", value=f"**{rec_mods} moderátorů**", inline=True)
        
        status_text = "✅ Komunita je zdravá a stabilní."
        if activity_rate < 0.05: status_text = "💤 Server vykazuje nízkou aktivitu (pod 5 %)."
        if mii_val is not None and mii_val > 0.02: status_text = "🚨 Vysoká moderační zátěž! Tým je pravděpodobně přetížen."
        
        embed.description = status_text
        
        if research:
            if research_data.get("success"):
                p_stay_active = research_data.get("retention_pct")
                p_inactive = research_data.get("inactivity_risk_pct")
                life_exp = research_data.get("activity_survival_expectancy_days")
                median_survival = research_data.get("median_activity_survival_days")
                
                life_exp_str = f"**{life_exp} dní**" if life_exp is not None else "**N/A**"
                median_survival_str = f"**{median_survival} dní**" if median_survival is not None else "**N/A**"
                p_stay_active_str = f"**{p_stay_active / 100.0:.1%}**" if p_stay_active is not None else "**N/A**"
                p_inactive_str = f"**{p_inactive / 100.0:.1%}**" if p_inactive is not None else "**N/A**"
                
                res_text = (
                    f"**Markovova analýza (Predikce 7 dní):**\n"
                    f"- Setrvání v aktivitě: {p_stay_active_str}\n"
                    f"- Odhad neaktivity: {p_inactive_str}\n\n"
                    f"**Analýza aktivity (Survival):**\n"
                    f"- Očekávaná doba setrvání v pozorované aktivitě: {life_exp_str}\n"
                    f"- Medián setrvání v aktivitě: {median_survival_str}"
                )
            else:
                res_text = "Nepodařilo se vypočítat výzkumná data (nedostatek historie nebo chyba zpracování)."
                
            embed.add_field(name="🧪 Výzkumná data (Markov/Survival)", value=res_text, inline=False)
            
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HealthCog(bot))
