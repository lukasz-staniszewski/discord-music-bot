import discord
from discord.ext import commands
import os
import re
from discord.ext.commands.bot import Bot
from discord.ext.commands.context import Context


class MessageCog(commands.Cog):
    def __init__(self, bot: Bot):
        """Message Cog constructor.

        Args:
            bot (Bot): Discord bot refference.
        """
        self.bot = bot
        self.BOTCHANNEL_ID = os.getenv("BOTCHANNEL_ID")

    @commands.command()
    async def brek(self, ctx: Context):
        """Bot sends funny message.

        Args:
            ctx (Context): Context of executed discord command.
        """
        await ctx.send("Widzisz mnie?! 👀")

    @commands.command()
    async def gif(self, ctx: Context):
        """Bot sends funny gif.

        Args:
            ctx (Context): Context of executed discord command.
        """
        await ctx.send(
            r"https://tenor.com/view/starege-dobrze-dobrzebrek-ca%C5%82y%C5%82eb-%C5%82eb-gif-22915280"
        )

    @commands.Cog.listener()
    async def on_message(self, message: str):
        """Reacting on specified emote.

        Args:
            message (str): Message sent.
        """
        if message.channel.id == int(self.BOTCHANNEL_ID):
            print(
                re.sub(r"#[0-9]+", "", str(message.author))
                + " wrote: "
                + message.content
            )
        possible_emote = re.findall(r"<:widziszmnie:[0-9]*>", message.content)
        if len(possible_emote) != 0:
            await message.add_reaction(possible_emote[0])
