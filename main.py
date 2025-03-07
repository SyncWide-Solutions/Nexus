import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from datetime import timedelta
import json

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

with open('banned_words.json', 'r') as f:
    banned_words = json.load(f)['banned_words']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

tree = bot.tree

@tasks.loop(seconds=1)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f"Currently on {len(bot.guilds)} Servers!"))

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'The bot is currently in {len(bot.guilds)} guilds.')
    await tree.sync()

# Add this event handler after the other commands
@bot.event
async def on_message(message):
    # Skip if message is from bot
    if message.author == bot.user:
        return

    # Check message content against banned words
    msg_content = message.content.lower()
    for word in banned_words:
        if word.lower() in msg_content:
            await message.delete()
            
            # Optional: Notify user their message was deleted
            embed = discord.Embed(
                title="Message Deleted",
                description=f"Your message contained a banned word.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=5)
            return

    # Important: Process commands after message check
    await bot.process_commands(message)

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

@tree.command(name='ban', description='Bans a user from the server.')
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided.'):
    try:
        dm = await member.create_dm()
        dm_embed = discord.Embed(title=f'You have been banned from {interaction.guild.name}.', 
                               description=f'Reason: {reason}\nModerator: {interaction.user.name}', 
                               color=discord.Color.red())
        await dm.send(embed=dm_embed)
    except discord.Forbidden:
        pass  # User has DMs disabled or has blocked the bot
    
    await member.ban(reason=reason)
    embed = discord.Embed(title=f'✅ {member.name} has been banned.', 
                         description=f'Reason: {reason}', 
                         color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@tree.command(name='unban', description='Unbans a user from the server.')
@commands.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, member: discord.Member):
    await member.unban()
    embed = discord.Embed(title=f'✅ {member.name} has been unbanned.', 
                         color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@tree.command(name='timeout', description='Timeouts a user on this server. Use format: 1d, 1w, 1m, 1y, 1h, 1min, 1sec')
@commands.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = 'No reason provided.'):
    # More precise time units mapping
    time_units = {
        's': 1,
        'sec': 1,
        'second': 1,
        'seconds': 1,
        'm': 60,
        'min': 60,
        'minute': 60,
        'minutes': 60,
        'h': 3600,
        'hour': 3600,
        'hours': 3600,
        'd': 86400,
        'day': 86400,
        'days': 86400,
        'w': 604800,
        'week': 604800,
        'weeks': 604800
    }
    
    # Extract number and unit from duration string
    amount = ''.join(filter(str.isdigit, duration))
    unit = ''.join(filter(str.isalpha, duration.lower()))
    
    if not amount or not unit:
        await interaction.response.send_message("Invalid format! Example: 1min, 30s, 2h, 1d")
        return
        
    if unit not in time_units:
        await interaction.response.send_message("Invalid time unit! Use: s/sec, m/min, h/hour, d/day, w/week")
        return
        
    seconds = int(amount) * time_units[unit]
    timeout_until = discord.utils.utcnow() + timedelta(seconds=seconds)
    
    try:
        dm = await member.create_dm()
        dm_embed = discord.Embed(
            title=f'You have been timed out in {interaction.guild.name}',
            description=f'Duration: {duration}\nReason: {reason}\nModerator: {interaction.user.name}',
            color=discord.Color.red()
        )
        await dm.send(embed=dm_embed)
    except discord.Forbidden:
        pass
    
    await member.timeout(timeout_until, reason=reason)
    embed = discord.Embed(
        title=f'✅ {member.name} has been timed out',
        description=f'Duration: {duration}\nReason: {reason}',
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# ADVERTISING COMMANDS

@tree.command(name='invite', description='Generates an invite link for the bot.')
async def invite(interaction: discord.Interaction):
    invite_link = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))
    embed = discord.Embed(title='Invite Link', description=f"[Click Here!](<{invite_link}>)", color=discord.Color.green())

    await interaction.response.send_message(embed=embed)

@tree.command(name='credits', description='Displays the bot credits.')
async def credits(interaction: discord.Interaction):
    embed = discord.Embed(title='Credits', description='This bot was created by [SyncWide Solutions](<https://github.com/SyncWide-Solutions>)\nLead Developer: [LolgamerHDDE](<https://github.com/LolgamerHDDE>)', color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
