<h1 align="center">Discord Music Bot</h1>
<h3 align="center">Łukasz Staniszewski</h1>

<div align="center">
<img src="https://user-images.githubusercontent.com/59453698/137017156-6e49745c-2c40-4d30-9abb-f2885e4afe25.gif" alt="banner">

</div>

<div align="center">
  Here is my personal discord bot which is playing music, working on multiple discord servers. Bot is hosted on heroku, you can feel free to invite him to your own discord server 🎶.
</div>

## Bot invitation to your own discord server:
1. Only you have to visit the site:
```
https://discord.com/oauth2/authorize?client_id=889117583935148102&scope=bot&permissions=0
```

## Used technologies:
1. Python 3.9.5
2. Discord.py 1.7.3
2. Heroku cloud platform.

## Instalation

1. Download this repository.
2. Create your own Python virtual environment.

``` 
python -m venv venv
```
3. Create powershell script with content:
```
$env:APP_ID = "[YOUR_BOT_ID_FROM_DISCORD_DEVELOPER_FORMAT"
$env:BOTCHANNEL_ID = [DEBUG_CHANNEL_ID]
```
3. Activate venv and powershell script in console.

``` 
REPO_PATH\venv\scripts\activate
REPO_PARH\script_name.ps1
```

4. Install necessary packages. 

``` 
pip install -r requirements.txt 
```

5. Run bot.

``` 
python discordBot.py 
```
