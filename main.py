import datetime
import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
# Get the token from the .env file and store it in a variable
TOKEN = os.getenv('bot_token') 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="=", 
    intents=intents, 
    case_insensitive=True  # <--- Add this line
)

# Added the decorator so the bot actually triggers this function
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

async def load_extensions():
    # Ensure 'market_cog.py' exists in the same folder
    try:
        await bot.load_extension('market_cog')
        print("Market Cog loaded successfully.")
    except Exception as e:
        print(f"Failed to load extension: {e}")

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command(aliases=['mmm','mm'])
@commands.has_permissions(moderate_members=True) # Only admins can use this!
async def mu(ctx, minutes: int = 3):
    member = ctx.author
    duration = datetime.timedelta(minutes=minutes)
    
    try:
        # 2. Apply the timeout
        await member.timeout(duration, reason=f"MU? MU? WHOPS {ctx.author}!")
        
        await ctx.send(f"🤐 **{member.display_name}** has been muted for {minutes} minutes. They cannot type or join VC. Womp Womp NIGGA")
        
    except Exception as e:
        await ctx.send(f"❌ Failed to mute user. Do I have 'Moderate Members' permissions? Error: {e}")


# async def main():
#     async with bot:
#         await load_extensions()
#         # Pass the VARIABLE 'TOKEN', not the STRING 'bot_token'
#         await bot.start(TOKEN)


async def setup_hook():
    await bot.load_extension('market_cog')




if __name__ == "__main__":
   # asyncio.run(main())
   bot.setup_hook = setup_hook
   bot.run(TOKEN)