# FOSNHU
# 2022, Fops Bot
# MIT License


import discord
import logging
import subprocess


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks


class bconsoleCog(commands.Cog, name="Bconsole"):
    def __init__(self, bot):
        self.bot = bot

        # Run the initalization script for bconsole
        subprocess.run("cd templates && ./inject.sh", shell=True)

    @app_commands.command(name="b")
    async def b(self, ctx: discord.Interaction, cmd: str):
        """
        Runs a bacula command.
        """

        out = subprocess.Popen(
            [
                f"echo {cmd} | bconsole"
            ],  # Use this command to get the messages out of bconsole
            stdout=subprocess.PIPE,  # Save the output
            stderr=subprocess.STDOUT,  # Save the output
            shell=True,
        )  # This is a already formatted shell command

        stdout, stderr = out.communicate()
        cleaned_stdout = (
            stdout.partition(b"\n" + bytes(cmd, "utf-8") + b"\n")[2] + b""
        ).decode(
            "utf-8"
        )  # Trim the messages by removing timestamp and connection info

        await ctx.response.send_message(f"```{cleaned_stdout}```")


async def setup(bot):
    await bot.add_cog(bconsoleCog(bot))
