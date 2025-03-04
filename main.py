import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

tree = bot.tree

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'The bot is currently in {len(bot.guilds)} guilds.')
    await tree.sync()

# TEST COMMANDS

@tree.command(name='ping', description='Checks if the bot is alive.')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong!')

# MODERATION COMMANDS

@tree.command(name='kick', description='Kicks a user from the server.')
@commands.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided.'):
    try:
        dm = await member.create_dm()
        dm_embed = discord.Embed(title=f'You have been kicked from {interaction.guild.name}.', 
                               description=f'Reason: {reason}\nModerator: {interaction.user.name}', 
                               color=discord.Color.red())
        await dm.send(embed=dm_embed)
    except discord.Forbidden:
        pass  # User has DMs disabled or has blocked the bot
    
    await member.kick(reason=reason)
    embed = discord.Embed(title=f'✅ {member.name} has been kicked.', 
                         description=f'Reason: {reason}', 
                         color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)