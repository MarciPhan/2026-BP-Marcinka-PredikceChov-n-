import discord
from discord.ext import commands
from typing import List, Optional

TITLE = "📘 Metricord - Analytics Bot"
FOOTER = "Metricord Bot – Analytics & Predictions"


PAGE_DATA = [
    {
        "name": "⚙️ Základní příkazy",
        "desc": (
            "**Ping** – `*ping` nebo `/ping`\n"
            "Zobrazí latenci bota a stav připojení\n\n"
            "**Help** – `*help` nebo `/help [modul]`\n"
            "Zobrazí tuto nápovědu\n"
            "Můžeš zadat název modulu pro přímý přechod\n"
        ),
    },
    {
        "name": "📊 Analytics - Activity Tracking",
        "desc": (
            "**Real-time sledování aktivity uživatelů**\n\n"
            "Bot automaticky trackuje:\n"
            "• Zprávy v kanálech\n"
            "• Voice aktivitu\n"
            "• Reakce a interakce\n"
            "• Join/Leave eventy\n\n"
            "Data se ukládají do Redis a jsou dostupná v dashboardu.\n"
        ),
    },
    {
        "name": "� Analytics - HyperLogLog Stats",
        "desc": (
            "**Efektivní counting pomocí HyperLogLog algoritmu**\n\n"
            "**Metriky:**\n"
            "• **DAU** (Daily Active Users) - denní aktivní uživatelé\n"
            "• **WAU** (Weekly Active Users) - týdenní aktivní\n"
            "• **MAU** (Monthly Active Users) - měsíční aktivní\n\n"
            "**Výhody HLL:**\n"
            "• Konstantní paměťová náročnost\n"
            "• Rychlé operace\n"
            "• Přesnost ~98%\n\n"
            "Všechny metriky jsou dostupné v web dashboardu.\n"
        ),
    },
    {
        "name": "🎯 Analytics - Predictions",
        "desc": (
            "**Predikce chování uživatelů (pro bakalářskou práci)**\n\n"
            "Bot sbírá data pro:\n"
            "• Predikci aktivity uživatelů\n"
            "• Analýzu engagement trendů\n"
            "• Detekci churn risk\n"
            "• Community health score\n\n"
            "**Dostupné v dashboardu:**\n"
            "• Grafy aktivity (Chart.js)\n"
            "• Predictions interface\n"
            "• User profily\n"
            "• Real-time metriky\n"
        ),
    },
    {
        "name": "📈 Analytics - Community Score",
        "desc": (
            "**Detailní výpočet skóre zdraví komunity (0-100)**\n\n"
            "Skóre se skládá ze 4 vážených složek (každá 25%):\n\n"
            "**1. Tým & Moderace (25%)**\n"
            "• Ideální poměr: **50-100 členů na moderátora**\n"
            "• Penalizace za nedostatek i přebytek moderátorů\n\n"
            "**2. Bezpečnost (25%)**\n"
            "• Level verifikace (max 60b)\n"
            "• Filtr explicitního obsahu (max 20b)\n"
            "• 2FA pro moderátory (20b)\n\n"
            "**3. Engagement (25%)**\n"
            "• **Participation Rate:** % denně aktivních členů\n"
            "• **Reply Ratio:** Poměr odpovědí ku všem zprávám (konverzace)\n"
            "• **Voice Activity:** Průměrný čas ve voice na aktivního uživatele\n\n"
            "**4. Aktivita Moderace (25%)**\n"
            "• Počet mod akcí (bany, kicky, timeouty) na 100 uživatelů\n"
            "• Hodnotí se přiměřenost (ani málo, ani moc)\n\n"
            "**Hodnocení:**\n"
            "🟢 **>80** Vynikající | 🔵 **>60** Dobrý | 🟠 **>40** Průměrný | 🔴 **<40** Nízký"
        ),
    },
    {
        "name": "� Web Dashboard",
        "desc": (
            "**Přístup:** http://localhost:8092\n\n"
            "**Funkce:**\n"
            "• Real-time metriky (DAU/MAU/WAU)\n"
            "• Interaktivní grafy aktivity\n"
            "• User analytics\n"
            "• Predictions & insights\n"
            "• OAuth přihlášení přes Discord\n\n"
            "**Technologie:**\n"
            "• FastAPI backend\n"
            "• Jinja2 templates\n"
            "• Chart.js grafy\n"
            "• Redis cache\n"
        ),
    },
]


class HelpPaginator(discord.ui.View):
    def __init__(self, author: discord.abc.User, pages: List[discord.Embed], start_index: int = 0, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.author = author
        self.pages = pages
        self.index = max(0, min(start_index, len(pages) - 1))
        self.message: Optional[discord.Message] = None

        options = [
            discord.SelectOption(label=self._clean_label(embed.title), value=str(i))
            for i, embed in enumerate(self.pages)
        ]
        self.select_menu.options = options

        self._refresh_button_states()

    def _clean_label(self, s: Optional[str]) -> str:
        return (s or "Untitled")[:100]

    async def _update(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Tohle ovládání patří tomu, kdo otevřel nápovědu.", ephemeral=True)
        self._refresh_button_states()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    def _refresh_button_states(self):
        self.prev_button.disabled = (self.index <= 0)
        self.next_button.disabled = (self.index >= len(self.pages) - 1)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = max(0, self.index - 1)
        await self._update(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = min(len(self.pages) - 1, self.index + 1)
        await self._update(interaction)

    @discord.ui.button(label="✖ Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Zavřít může jen autor nápovědy.", ephemeral=True)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.select(placeholder="Přejít na modul…")
    async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            target = int(select.values[0])
        except Exception:
            target = 0
        self.index = max(0, min(target, len(self.pages) - 1))
        await self._update(interaction)

    async def on_timeout(self):
        if self.message:
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class HelpCustom(commands.Cog):
    """Zobrazí přehled Metricord analytics bota."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_pages(self) -> List[discord.Embed]:
        pages: List[discord.Embed] = []
        total = len(PAGE_DATA)
        for i, page in enumerate(PAGE_DATA, start=1):
            embed = discord.Embed(
                title=page["name"],
                description=page["desc"],
                color=discord.Color.blue()
            )
            embed.set_author(name=TITLE)
            embed.set_footer(text=f"{FOOTER} • {i}/{total}")
            if self.bot.user and self.bot.user.display_avatar:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            pages.append(embed)
        return pages

    @commands.hybrid_command(name="help", description="Zobrazí přehled Metricord analytics bota")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def help_command(self, ctx: commands.Context, modul: Optional[str] = None):
        """
        /help [modul]  |  *help [modul]
        - modul: substring názvu stránky (case-insensitive), otevře daný modul.
        """
        pages = self.build_pages()

        index = 0
        if modul:
            m = modul.lower().strip()
            for i, e in enumerate(pages):
                if m in (e.title or "").lower():
                    index = i
                    break

        view = HelpPaginator(author=ctx.author, pages=pages, start_index=index, timeout=180.0)

        if isinstance(ctx.interaction, discord.Interaction):
            await ctx.interaction.response.send_message(embed=pages[index], view=view, ephemeral=True)
            view.message = await ctx.interaction.original_response()
        else:
            msg = await ctx.send(embed=pages[index], view=view)
            view.message = msg

async def setup(bot: commands.Bot):
    # remove default help
    if "help" in bot.all_commands:
        bot.remove_command("help")
    await bot.add_cog(HelpCustom(bot))
