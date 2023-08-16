# FOSNHU
# 2022, Fops Bot
# MIT License


import os
import discord
import logging


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands


class ToolCog(commands.Cog, name="Tools"):
    def __init__(self, bot):
        self.bot = bot

        # Args
        self.alertUser = int(os.environ.get("ALERT_USER"))

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.message.Message):
        if (
            isinstance(ctx.channel, discord.channel.DMChannel)
            and not ctx.author.bot
            and not ctx.author.id == self.alertUser
        ):
            logging.info(
                f"Got private message in {ctx.channel.id}, author was {ctx.author.name}, forwarding it!"
            )

            user = await self.bot.fetch_user(self.alertUser)
            await user.send(
                f"Private message from {ctx.author.name}\n```{ctx.content}```"
            )

            await ctx.add_reaction("📧")

    @app_commands.command(name="version")
    async def version(self, ctx: discord.Interaction):
        """
        Prints the revision/version.
        """

        await ctx.response.send_message(f"I am running version `{self.bot.version}`.")

    @commands.command()
    @commands.guild_only()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        """
        From here https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot):
    await bot.add_cog(ToolCog(bot))
