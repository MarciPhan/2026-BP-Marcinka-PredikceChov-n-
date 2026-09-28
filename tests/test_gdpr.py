import pytest
from unittest.mock import AsyncMock, MagicMock
import fakeredis.aioredis

from bot.commands.gdpr import GDPRCommands


def _make_cog():
    bot = MagicMock()
    bot.get_guild.return_value = None  # force the "Server {id}" fallback name
    cog = GDPRCommands(bot=bot)
    cog.r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return cog


def _make_interaction(user_id="42"):
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_gdpr_export_includes_manual_role_review_note():
    """A GDPR export must include the manual admin note/judgement stored about
    the requesting user, since it is personal data about them too (FR-17/NFR-01)."""
    cog = _make_cog()
    interaction = _make_interaction(user_id="42")
    guild_id = "999"

    await cog.r.sadd("bot:guilds", guild_id)
    await cog.r.hset(f"health:role_review:{guild_id}:42", mapping={
        "judgement": "positive",
        "note": "Aktivní a nápomocný člen.",
        "reviewed_by": "1",
        "reviewed_at": "2026-01-01T00:00:00",
    })

    await cog.gdpr_export.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    embed = interaction.followup.send.await_args.kwargs["embed"]
    guild_field = next(f for f in embed.fields if guild_id in f.name or "Server" in f.name)
    assert "positive" in guild_field.value
    assert "Aktivní a nápomocný" in guild_field.value


@pytest.mark.asyncio
async def test_gdpr_delete_removes_manual_role_review_note():
    """A GDPR deletion request must also remove the manual admin note/judgement
    about the user -- previously this key survived /gdpr delete."""
    cog = _make_cog()
    guild_id = "999"
    user_id = "42"
    review_key = f"health:role_review:{guild_id}:{user_id}"

    await cog.r.sadd("bot:guilds", guild_id)
    await cog.r.hset(review_key, mapping={"judgement": "neutral", "note": "n/a"})
    assert await cog.r.exists(review_key)

    view = None
    for attr_name in dir(cog.gdpr_delete):
        pass  # placeholder to keep lint quiet if unused

    # Build the confirmation view the same way the /gdpr delete command does,
    # then invoke its "confirm" button callback directly.
    from bot.commands.gdpr import GDPRCommands as _GDPRCommands  # noqa: F401

    class _Interaction:
        def __init__(self, uid):
            self.user = MagicMock(id=uid)
            self.response = MagicMock()
            self.response.defer = AsyncMock()
            self.followup = MagicMock()
            self.followup.send = AsyncMock()
            self.message = MagicMock()
            self.message.edit = AsyncMock()

    confirm_interaction = _Interaction(user_id)

    # Re-create the ConfirmView the same way gdpr_delete does, by calling the
    # command and capturing the view passed to interaction.response.send_message.
    open_interaction = _Interaction(user_id)
    open_interaction.response.send_message = AsyncMock()
    await cog.gdpr_delete.callback(cog, open_interaction)
    _, kwargs = open_interaction.response.send_message.await_args
    view = kwargs["view"]

    confirm_button = next(item for item in view.children if "smazat" in item.label.lower())
    await confirm_button.callback(confirm_interaction)

    assert not await cog.r.exists(review_key)
