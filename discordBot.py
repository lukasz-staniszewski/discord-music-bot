import discord
import os
from discord.ext import commands
from musicBot import MusicCog
from messageBot import MessageCog

APP_ID = os.getenv("APP_ID")

bot = commands.Bot(command_prefix="!")
bot.add_cog(MusicCog(bot))
bot.add_cog(MessageCog(bot))

bot.run(APP_ID)
