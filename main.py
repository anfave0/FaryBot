import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from keep_alive import keep_alive

from keep_alive import keep_alive

load_dotenv() 
token= os.getenv('TOKEN') 

intents = discord.Intents.default()
intents.message_content = True  

bot = commands.Bot(command_prefix="!", intents=intents) #Ajoute "!" pour dmd une commande


token = os.environ['TOKEN']
keep_alive()
bot.run(token)