import discord
from discord.ext import commands
import os
import re


class MessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BOTCHANNEL_ID = os.getenv("BOTCHANNEL_ID")

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
        possible_emote = re.findall(r"<:widziszmnie:[0-9]*>", message.content)
        if len(possible_emote) != 0:
            await message.add_reaction(possible_emote[0])
