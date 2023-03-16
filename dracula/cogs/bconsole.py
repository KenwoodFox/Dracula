# FOSNHU
# 2022, Fops Bot
# MIT License


import discord
import logging
import os
import subprocess


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks


class bconsoleCog(commands.Cog, name="Bconsole"):
    def __init__(self, bot):
        self.bot = bot

        # Run the initalization script for bconsole
        subprocess.run("cd templates && ./inject.sh", shell=True)

        # Setup "static" channels
        chanid = int(os.environ.get("CHANNEL"))
        self.alertUser = int(os.environ.get("ALERT_USER"))
        self.alertChan = self.bot.get_channel(chanid)

        # Setup tasks
        self.upcoming_events.start()

    def bconsoleCommand(self, cmd: str):
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

        return cleaned_stdout

    @tasks.loop(seconds=20)
    async def upcoming_events(self):
        messages = self.bconsoleCommand("messages")

        if not "You have no messages." in messages:
            logging.debug(f"Reporting on {messages}.")
            if "Please mount" in messages:
                await self.alertChan.send(f"<@{self.alertUser}>\n```{messages}```")
            else:
                await self.alertChan.send(f"```{messages}```")
        else:
            logging.debug("No messages to report.")

    @app_commands.command(name="bcmd")
    @commands.has_role("SYSADMIN")
    async def bcmd(self, ctx: discord.Interaction, cmd: str):
        """
        Runs a bacula command.
        """

        maxCharPerMessage = 1900
        raw = self.bconsoleCommand(cmd)

        output = [
            raw[i : i + maxCharPerMessage]
            for i in range(0, len(raw), maxCharPerMessage)
        ]

        await ctx.response.send_message(f"Running command `{cmd}`\n```{output[0]}```")

        if len(output) > 1:
            for part in output[1:]:
                await self.alertChan.send(f"```{part}```")


async def setup(bot):
    await bot.add_cog(bconsoleCog(bot))
