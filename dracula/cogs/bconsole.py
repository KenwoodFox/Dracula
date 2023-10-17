# Bconsole Cog
# 2023, Dracula Bot
# MIT License


import discord
import logging
import re
import os
import time
import subprocess
import paramiko
import yaml
import shutil


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

        # Setup user config
        confPath = "/app/config/config.yaml"
        if not os.path.isfile(confPath):
            logging.warn("Config not found! Copying default")
            shutil.copyfile("/app/templates/config.yaml", confPath)

        # Static or at least, infrequently updated data
        with open(confPath, "r") as file:
            self.yamlConf = yaml.safe_load(file)
        self.globalStats = []
        self.lastContent = ""  # Used to prevent double posting
        self.lastContentCt = 0

        # Setup tasks
        self.check_messages.start()
        self.get_global_stats.start()

    def sizeof_fmt(self, num):
        for unit in ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"):
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num} Bytes"

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

    def extract(self, data):
        """
        Extract targets from text!
        """

        myDict = {}

        for line in data:
            splitLines = line.split("   ")

            thisLine = []
            for nugget in splitLines:
                if nugget != "":
                    thisLine.append(nugget.lstrip())

            if len(thisLine) >= 2:
                myDict[thisLine[0]] = thisLine[1]

        return myDict

    async def sendSummary(self, data):
        if data is None:
            logging.error("Not sending summary because no data was sent.")
            return

        userData = self.yamlConf["users"]

        for user in userData:
            userId = None
            jobNames = userData[user]["user-jobs"]

            for jobName in jobNames:
                if jobName in data["Job:"]:
                    userId = userData[user]["discord"]
                    logging.info(f"Found job {jobName} for user {userId}")

            if userId == None:
                logging.debug("Not sending summary because userid is not in dict.")
                return

            user = await self.bot.fetch_user(userId)
            try:
                logging.info(f"Fetched user {user.name} from id {userId}")
            except:
                logging.warn("Couldn't get valid username, line 120 in bconsole.py")
            term = data["Termination:"]
            bytesWritten = re.search(r"\((.*?)\)", data["SD Bytes Written:"]).group(1)

            # Start by crafting an embed
            if term == "Backup OK":
                color = 0x76FF26
            else:
                color = 0x7A0C1F

            embed = discord.Embed(
                title=data["Job:"],
                color=color,
            )

            embed.add_field(
                name="Status",
                value=term,
                inline=False,
            )

            embed.add_field(
                name="Files Backed Up",
                value=data["SD Files Written:"],
                inline=True,
            )

            embed.add_field(
                name="Bytes Written",
                value=bytesWritten,
                inline=True,
            )

            embed.add_field(
                name="Time Consumed",
                value=data["Elapsed time:"],
                inline=True,
            )

            embed.add_field(
                name="Volumes",
                value=data["Volume name(s):"],
                inline=False,
            )

            embed.set_footer(text=f"Bot Version {self.bot.version}")

            # Send the embed!
            await user.send(embed=embed)

    @app_commands.command(name="mystatus")
    async def mystatus(self, ctx: discord.Interaction):
        """
        Get your personal stats
        """

        # Get the config userdata
        userData = self.yamlConf["users"]
        numJobs = 0  # Number of jobs we found
        backupUserBytesTotal = 0  # Backup bytes for this user
        backupBytesTotal = 0  # Backup bytes overall

        # Make new embed
        embed = discord.Embed(
            title=f"Backup Stats for {ctx.user.name}",
            color=0x76FF26,
        )

        # Example Data
        exampleLine = [
            "",
            "   46 ",
            "     6,365 ",
            " 60161962240   ",
            " BackupDatabase     ",
            "",
        ]

        # Process the lines
        for line in self.globalStats:
            line = line.split("|")  # Split on delim

            # Try cracking the max line
            try:
                backupBytesTotal = int(line[3])
            except:
                pass

            if not (len(line) < len(exampleLine)):  # if line is correct size
                for user in userData:  # Check every user in userData
                    # Get the list of this user's jobs
                    jobNames = userData[user]["user-jobs"]

                    # Check if this user is ours
                    if userData[user]["discord"] == ctx.user.id:
                        for jobName in jobNames:
                            # Check if their jobname shows up in spot 4
                            if jobName in line[4]:
                                numJobs += 1  # We found stats to report on!

                                thisJobBytes = int(line[3])
                                backupUserBytesTotal += thisJobBytes

                                # Add an embed field to the report
                                embed.add_field(
                                    name=jobName,
                                    value=f"{self.sizeof_fmt(thisJobBytes)}",
                                    inline=True,
                                )

        embed.add_field(
            name="",
            value=f"Your {numJobs} backup{'s' if numJobs > 1 else ''} consume{'s' if numJobs == 1 else ''} {self.sizeof_fmt(backupUserBytesTotal)}, {(backupUserBytesTotal/backupBytesTotal):.2%} of total backup data ({self.sizeof_fmt(backupBytesTotal)}).",
            inline=False,
        )

        embed.set_footer(text=f"Bot Version {self.bot.version}")

        # Send the embed!
        if numJobs > 0:
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.response.send_message("No stats found for your user!")

    @tasks.loop(seconds=900)
    async def get_global_stats(self):
        # Get global Stat data from bacula
        logging.debug("Getting global stats.")
        if True:
            self.globalStats = self.bconsoleCommand("list jobtotals").split("\n")
        else:
            with open("/app/templates/testData.txt") as f:
                self.globalStats = [line.rstrip("\n") for line in f]

    @tasks.loop(seconds=20)
    async def check_messages(self):
        maxCharPerMessage = 1900
        raw = self.bconsoleCommand("messages")

        # await self.sendSummary("Backup-Joe", "180", "4mb")

        if True:
            lines = raw.split("\n")  # A list containing every line
        else:
            with open("/app/templates/testData.txt") as f:
                lines = [line.rstrip("\n") for line in f]

        # Dont report empty messages
        if "You have no messages." in lines[0]:
            return

        # Collect/parse some report data
        try:
            data = self.extract(lines)
        except:
            data = None

        content = ""  # The content of a single message we're going to send
        for idx, line in enumerate(lines):
            # Will adding this line take us over the limit?
            if len(content) + len(line) < maxCharPerMessage:
                # Add this line
                content += line + "\n"

                # If this is not the last line
                if idx != len(lines) - 1:
                    continue  # Skip to the next "for" iterator

            if self.lastContent != content:  # Check if we're double posting
                if "Please mount" in content:
                    await self.alertChan.send(f"<@{self.alertUser}>\n```{content}```")
                else:
                    await self.alertChan.send(f"```{content}```")

                if "Termination:" in content:
                    # its time to send an alert!
                    try:
                        await self.sendSummary(data)
                    except Exception as e:
                        logging.error(f"Error sending data! Error was {e}")

                self.lastContent = content
                self.lastContentCt = 0
                content = line + "\n"
            else:
                self.lastContentCt += 1

                # What to do if we are double-posting
                last_message = await self.alertChan.fetch_message(
                    self.alertChan.last_message_id
                )  # Get last message

                if last_message.author == self.bot.user and self.lastContentCt != 0:
                    await last_message.delete()

                await self.alertChan.send(
                    f"```Message Repeated {self.lastContentCt} times.```"
                )

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
