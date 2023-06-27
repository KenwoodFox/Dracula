# FOSNHU
# 2022, Fops Bot
# MIT License


import discord
import logging
import os
import time
import subprocess
import paramiko


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
        maxCharPerMessage = 1900
        raw = self.bconsoleCommand("messages")

        messages = [
            raw[i : i + maxCharPerMessage]
            for i in range(0, len(raw), maxCharPerMessage)
        ]

        if not "You have no messages." in messages[0]:
            logging.debug(f"Reporting on {messages[0]}.")
            if "Please mount" in messages[0]:
                await self.alertChan.send(f"<@{self.alertUser}>\n```{messages[0]}```")
            else:
                await self.alertChan.send(f"```{messages[0]}```")
        else:
            logging.debug("No messages to report.")

        if len(messages) > 1:
            for part in messages[1:]:
                await self.alertChan.send(f"```{part}```")

    @app_commands.command(name="eject")
    @commands.has_role("SYSADMIN")
    async def eject(self, ctx: discord.Interaction):
        await ctx.response.defer()  # Defer client (dont crash if this takes a while)
        ssh = paramiko.SSHClient()  # Spawn an SSH client
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = os.environ.get("ADDRESS")
        user = os.environ.get("SSH_USER")
        pwd = os.environ.get("SSH_PASSWORD")

        # First ask bacula to unmount the tape
        raw = self.bconsoleCommand("unmount")
        time.sleep(1)  # Wait a second
        await ctx.followup.send(f"```{raw}```")

        # Connect and eject the tape
        ssh.connect(host, username=user, password=pwd)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("mt -f /dev/sa0 offline")
        time.sleep(2)

        if len(ssh_stdout.read().decode("utf-8")) == 0:
            await ctx.followup.send("Tape is ejected!")
        else:
            await ctx.followup.send("Tape is ejected! (I think)")

    @app_commands.command(name="bcmd")
    @commands.has_role("SYSADMIN")
    async def bcmd(self, ctx: discord.Interaction, cmd: str):
        """
        Runs a bacula command.
        """

        await ctx.response.defer()  # We can expect that this command will take a while

        maxCharPerMessage = 1900
        raw = self.bconsoleCommand(cmd)

        lines = raw.split("\n")  # A list containing every line

        content = f"Running command `{cmd}`\n```"  # The content of a single message we're going to send
        for line in lines:
            if len(content) + len(line) < maxCharPerMessage:
                content += line + "\n"
            else:
                await ctx.followup.send(f"{content}```")
                content = "```"

        if content != "```":
            await ctx.followup.send(f"{content}```")


async def setup(bot):
    await bot.add_cog(bconsoleCog(bot))
