
import discord
import re
import os

BOTCHANNEL_ID = os.getenv("BOTCHANNEL_ID")
WIDZISZMNIE_EMOTE = os.getenv("WIDZISZMNIE_EMOTE")
APP_ID = os.getenv("APP_ID")
client = discord.Client()

print(APP_ID)
print(type(APP_ID))

@client.event
async def on_message(message):
    if message.channel.id == BOTCHANNEL_ID:
        print(re.sub(r'#[0-9]+','',str(message.author)) + " wrote: " + message.content)
    if message.content.find("!brek") != -1:
        await message.channel.send("Widzisz mnie?! 👀")
    if message.content.find("!gif") != -1:
        await message.channel.send(r"https://tenor.com/view/starege-dobrze-dobrzebrek-ca%C5%82y%C5%82eb-%C5%82eb-gif-22915280")
    if message.content.find(WIDZISZMNIE_EMOTE) != -1 and str(message.author) != "DJ WidziszMnie#0843":
        await message.add_reaction(WIDZISZMNIE_EMOTE)


client.run(APP_ID)
