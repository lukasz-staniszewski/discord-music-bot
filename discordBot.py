import discord
import os
from discord.ext import commands
from src.musicBot import MusicCog
from src.messageBot import MessageCog

APP_ID = os.getenv("APP_ID")

bot = commands.Bot(command_prefix="!", help_command=None)
bot.add_cog(MusicCog(bot))
bot.add_cog(MessageCog(bot))

bot.run(APP_ID)
