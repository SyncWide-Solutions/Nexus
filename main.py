import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from datetime import timedelta
import json
import openai
import asyncio

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

with open('banned_words.json', 'r') as f:
    banned_words = json.load(f)['banned_words']

with open('help.json', 'r') as f:
    help_commands = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

tree = bot.tree

# UPDATE PRESENCE

@tasks.loop(seconds=1)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f"Currently on {len(bot.guilds)} Servers!"))

# BOT STARTUP

@tasks.loop(seconds=1)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f'Currently on {len(bot.guilds)} servers!'))

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'The bot is currently in {len(bot.guilds)} guilds.')
    update_presence.start()
    await tree.sync()
    await update_presence.start()

# WORD FILTERING

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

# PING COMMAND

@tree.command(name='ping', description='Checks if the bot is alive.')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong!')

# GENERAL COMMANDS

# HELP COMMAND

@tree.command(name='help', description='Displays a list of available commands and descriptions.')
async def help(interaction: discord.Interaction):
    help_embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())

    # Loop through the help_commands dictionary and add each command to the embed
    for command, details in help_commands.items():
        description = details["description"]
        usage = details.get("usage", None)
        field_value = f"{description}\n**Usage:** {usage}" if usage else description
        help_embed.add_field(name=command, value=field_value, inline=False)

    await interaction.response.send_message(embed=help_embed)

# MODERATION COMMANDS

# KICK COMMAND

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

# BAN COMMAND

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

# UNBAN COMMAND

@tree.command(name='unban', description='Unbans a user from the server.')
@commands.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, member: discord.Member):
    await member.unban()
    embed = discord.Embed(title=f'✅ {member.name} has been unbanned.', 
                         color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# TIMEOUT COMMAND

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
        dm_embed = discord.Embed(title=f'You have been timeouted from {interaction.guild.name}.', 
                            description=f'Reason: {reason}\nModerator: {interaction.user.name}\nDuration: {duration}', 
                            color=discord.Color.red())
        dm_embed = discord.Embed(
            title=f'You have been timed out in {interaction.guild.name}',
            description=f'Duration: {duration}\nReason: {reason}\nModerator: {interaction.user.name}',
            color=discord.Color.red()
        )
        await dm.send(embed=dm_embed)
    
    except discord.Forbidden:
        pass
    
    await member.timeout(timeout_until, reason=reason)  # Changed to positional argument
    embed = discord.Embed(title=f'✅ {member.name} has been timeouted.', 
                         description=f'Reason: {reason}\nDuration: {duration}', 
                         color=discord.Color.green())
    await member.timeout(timeout_until, reason=reason)
    embed = discord.Embed(
        title=f'✅ {member.name} has been timed out',
        description=f'Duration: {duration}\nReason: {reason}',
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# COSTUMIZATION COMMANDS

# NUKE COMMAND

@tree.command(name='nuke', description='Deletes messages in a channel.')
@commands.has_permissions(manage_messages=True, manage_channels=True, read_message_history=True)
async def nuke(interaction: discord.Interaction, message_count: int = None):
    if message_count is None:
        count = None
    else:
        count = message_count + 1

    await interaction.channel.purge(limit=count)

    if message_count is None:
        count = "All"
    else:
        count = str(message_count)

    embed = discord.Embed(title=f'✅ {count} Messages deleted.', color=discord.Color.green())
    await interaction.channel.send(embed=embed)

# PREMIUM COMMANDS

# CHECK FOR ACTIVE SUBSCRIPTION

@tree.command(name='check', description='Checks for an active subscription.')
async def check_subscription(interaction: discord.Interaction):
    application_id = bot.application_id  # Get the bot's application ID
    user_id = interaction.user.id

    # Manually fetch entitlements using the bot's HTTP client
    data = await bot.http.get_entitlements(application_id)

    if not data:
        not_data_embed = discord.Embed(title='Error', description='❌ No entitlements found.', color=discord.Color.red())
        await interaction.response.send_message(embed=not_data_embed)
        return

    # Check if user has an active entitlement
    for entitlement in data:
        if entitlement["user_id"] == str(user_id) and entitlement["sku_id"] == "1347585991975637132":
            active_embed = discord.Embed(title='Success', description='✅ You have an active subscription!', color=discord.Color.green())
            await interaction.response.send_message(embed=active_embed)
            return

    not_active_embed = discord.Embed(title='Error', description='❌ No entitlements found.', color=discord.Color.red())
    await interaction.response.send_message(embed=not_active_embed)

# RADIO COMMAND

@tree.command(name='radio', description='Plays a radio station.')
async def radio(interaction: discord.Interaction, station: str = 'http://radio.syncwi.de:8000/stream.aac'):
    application_id = bot.application_id  # Get the bot's application ID
    user_id = interaction.user.id

    # Manually fetch entitlements using the bot's HTTP client
    data = await bot.http.get_entitlements(application_id)

    if not data:
        not_data_embed = discord.Embed(title='Error', description='❌ No entitlements found.', color=discord.Color.red())
        await interaction.response.send_message(embed=not_data_embed)
        return

    # Check if user has an active entitlement
    has_subscription = any(entitlement["user_id"] == str(user_id) and entitlement["sku_id"] == "1347585991975637132" for entitlement in data)

    if not has_subscription:
        error_embed = discord.Embed(title='Error', description='❌ You do not have an active subscription.', color=discord.Color.red())
        await interaction.response.send_message(embed=error_embed)
        return

    # Get the user's voice channel
    voice_channel = interaction.user.voice.channel if interaction.user.voice else None
    if not voice_channel:
        no_channel_embed = discord.Embed(title='Error', description='❌ You need to join a voice channel first.', color=discord.Color.red())
        await interaction.response.send_message(embed=no_channel_embed)
        return

    # Join the voice channel
    vc = await voice_channel.connect()

    # Start playing the radio stream using FFmpeg
    try:
        vc.play(
            discord.FFmpegPCMAudio(station),  # The radio stream URL
            after=lambda e: print(f'Error occurred: {e}')  # Handle errors
        )
        
        active_embed = discord.Embed(title='Success', description=f'✅ Playing {station} in {voice_channel.name}.', color=discord.Color.green())
        await interaction.response.send_message(embed=active_embed)
        
        # Wait until the audio finishes playing or until the user disconnects
        while vc.is_playing():
            await asyncio.sleep(1)

        # Disconnect the bot after the stream ends
        await vc.disconnect()
    except Exception as e:
        error_embed = discord.Embed(title='Error', description=f'❌ Failed to play the radio station: {str(e)}', color=discord.Color.red())
        await interaction.response.send_message(embed=error_embed)

# DISCONNECT COMMAND

@tree.command(name='disconnect', description='Disconnects the bot from the voice channel.')
async def disconnect(interaction: discord.Interaction):
    # Get the bot's voice channel
    voice_channel = bot.voice_clients[0] if bot.voice_clients else None
    # Disconnect the bot from the voice channel
    try:
        await voice_channel.disconnect()
        disconnect_embed = discord.Embed(title='Success', description='✅ Disconnected from the voice channel.', color=discord.Color.green())
        await interaction.response.send_message(embed=disconnect_embed)
    except Exception as e:
        error_embed = discord.Embed(title='Error', description=f'❌ Failed to disconnect: {str(e)}', color=discord.Color.red())
        await interaction.response.send_message(embed=error_embed)

# AI COMMAND

@tree.command(name='ai', description='Generates an AI response.')
async def ai(interaction: discord.Interaction, prompt: str):
    application_id = bot.application_id  # Get the bot's application ID
    user_id = interaction.user.id

    # Manually fetch entitlements using the bot's HTTP client
    data = await bot.http.get_entitlements(application_id)

    if not data:
        not_data_embed = discord.Embed(title='Error', description='❌ No entitlements found.', color=discord.Color.red())
        await interaction.response.send_message(embed=not_data_embed)
        return

    # Check if user has an active entitlement
    has_subscription = any(entitlement["user_id"] == str(user_id) and entitlement["sku_id"] == "1347585991975637132" for entitlement in data)

    if not has_subscription:
        error_embed = discord.Embed(title='Error', description='❌ You do not have an active subscription.', color=discord.Color.red())
        await interaction.response.send_message(embed=error_embed)
        return

    # Generate AI response using OpenAI
    await interaction.response.defer()  # Defer response to allow processing time
    try:
        client = openai.OpenAI()  # Create OpenAI client
        ai_response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = ai_response.choices[0].message.content

        embed = discord.Embed(title="AI Response", description=response_text, color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

    except Exception as e:
        exception_embed = discord.Embed(title='Error', description=f"⚠️ Error generating response: {str(e)}", color=discord.Color.red())
        await interaction.followup.send(embed=exception_embed)

# ADVERTISING COMMANDS

# INVITE COMMAND

@tree.command(name='invite', description='Generates an invite link for the bot.')
async def invite(interaction: discord.Interaction):
    invite_link = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))
    embed = discord.Embed(title='Invite Link', description=f"[Click Here!](<{invite_link}>)", color=discord.Color.green())

    await interaction.response.send_message(embed=embed)

# CREDITS COMMAND

@tree.command(name='credits', description='Displays the bot credits.')
async def credits(interaction: discord.Interaction):
    embed = discord.Embed(title='Credits', description='This bot was created by [SyncWide Solutions](<https://github.com/SyncWide-Solutions>)\nLead Developer: [LolgamerHDDE](<https://github.com/LolgamerHDDE>)', color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# LEGAL COMMAND

@tree.command(name='legal', description='Displays the bot legal information.')
async def legal(interaction: discord.Interaction):
    embed = discord.Embed(title='Nexus Legal Info', description=f'Here are the Legal Links for the bot {bot.user.name}:\n\nTerms Of Service (ToS): [Click Here](<https://syncwi.de/terms-of-service.html>)\nPrivacy Policy: [Click Here](<https://syncwi.de/privacy-policy.html>)\nContact: [Click Here](<https://syncwi.de/contact.html>)\n\n**Next Info only Relevant for Developers!**\n\nThe {bot.user.name} Bot is Licensed under the [MIT License](<https://opensource.org/license/mit>) which you can view by [Clicking Here](<https://github.com/SyncWide-Solutions/Nexus/blob/main/LICENSE>)', color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)

# This should be the 1000th line of code (goal).