import discord
from discord.ext import commands
import os
import re


class MessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BOTCHANNEL_ID = os.getenv("BOTCHANNEL_ID")
        self.WIDZISZMNIE_EMOTE = os.getenv("WIDZISZMNIE_EMOTE")

    @commands.command()
    async def brek(self, ctx):
        await ctx.send("Widzisz mnie?! 👀")

    @commands.command()
    async def gif(self, ctx):
        await ctx.send(
            r"https://tenor.com/view/starege-dobrze-dobrzebrek-ca%C5%82y%C5%82eb-%C5%82eb-gif-22915280"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == int(self.BOTCHANNEL_ID):
            print(
                re.sub(r"#[0-9]+", "", str(message.author))
                + " wrote: "
                + message.content
            )
        if (
            message.content.find(self.WIDZISZMNIE_EMOTE) != -1
            and str(message.author) != "DJ WidziszMnie#0843"
        ):
            await message.add_reaction(self.WIDZISZMNIE_EMOTE)
