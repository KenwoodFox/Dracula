# Kitsune Robotics
# 2022, Bacubot
# MIT License


import discord
import logging
import asyncio

from discord.ext import commands


class BaculaCog(commands.Cog, name="Tools"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        status_channel = self.bot.get_channel(666872163030007808)

        await self.bot.get_guild(505468527503867904).me.edit(nick="Bacubot")

        await status_channel.send(
            f"Bacubot version `{self.bot.version}` just restarted."
        )

    @commands.command()
    async def version(self, ctx, *, member: discord.Member = None):
        """
        Prints the revision/version.

        Ex: ^version

        Written by Joe.
        """

        await ctx.send(f"I am running version `{self.bot.version}`.")


async def setup(bot):
    await bot.add_cog(BaculaCog(bot))
