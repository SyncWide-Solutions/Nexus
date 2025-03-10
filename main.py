import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from datetime import timedelta, datetime
import json
import openai
import asyncio
import random
import logging
import mysql.connector
from mysql.connector import Error
from logging.handlers import TimedRotatingFileHandler

# Add these to your existing environment variables
DB_HOST = "45.84.196.164"
DB_USER = "syncwide"
DB_PASSWORD = "1Subfuerlinus!"
DB_NAME = "main"

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
def setup_logger():
    logger = logging.getLogger('nexus')
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create daily rotating file handler
    log_file = f'logs/{datetime.now().strftime("%d.%m.%Y")}.log'
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()

with open('banned_words.json', 'r') as f:
    banned_words = json.load(f)['banned_words']

with open('help.json', 'r') as f:
    help_commands = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

bot.logger = logger

tree = bot.tree

# UPDATE PRESENCE

@tasks.loop(seconds=1)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f"Currently on {len(bot.guilds)} Servers!"))

# BOT STARTUP

@tasks.loop(seconds=60)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f'Currently on {len(bot.guilds)} servers!'))

@bot.event
async def on_ready():
    bot.logger.info(f'{bot.user.name} has connected to Discord!')
    bot.logger.info(f'The bot is in {len(bot.guilds)} servers.')
    await tree.sync()
    await update_presence.start()

# WORD FILTERING

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg_content = message.content.lower()
    for word in banned_words:
        if word.lower() in msg_content:
            await message.delete()
            bot.logger.warning(f'Deleted message from {message.author} containing banned word')
            embed = discord.Embed(
                title="Message Deleted",
                description=f"Your message contained a banned word.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=5)
            return

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
    bot.logger.info(f'{interaction.user} kicked {member} from server {interaction.guild.name} for reason: {reason}')
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
    bot.logger.info(f'{interaction.user} banned {member} from server {interaction.guild.name} for reason: {reason}')
    embed = discord.Embed(title=f'✅ {member.name} has been banned.', 
                         description=f'Reason: {reason}', 
                         color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# UNBAN COMMAND

@tree.command(name='unban', description='Unbans a user from the server.')
@commands.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, member: discord.Member):
    await member.unban()
    bot.logger.info(f'{interaction.user} unbanned {member} from server {interaction.guild.name}')
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
    timeout_until = discord.utils.now(datetime.timezone.utc) + timedelta(seconds=seconds)

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
    bot.logger.info(f'{interaction.user} timed out {member} in server {interaction.guild.name} for reason: {reason}')
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
    bot.logger.info(f'{interaction.user} nuked channel {interaction.channel.name} in server {interaction.guild.name}')
    await interaction.channel.send(embed=embed)

# CREATE EMBED COMMAND

@tree.command(name='embed', description='Creates a coustomizable Embed')
async def create_embed(interaction: discord.Interaction, title: str = None, description: str = None, color: str = None, timestamp: bool = False):
    if timestamp == True:
        discord_ts = datetime.now()
    else:
        discord_ts = None

    if color != None:
        color = discord.Color(int(color.strip('#'), 16))
    else:
        color = None

    embed = discord.Embed(title=title, description=description, timestamp=discord_ts, color=color)
    try:
        await interaction.response.send_message(embed=embed)
    except discord.DiscordException as e:
        error_embed = discord.Embed(title='❌ Error whilst sending Embed', description=f'Error description: {e}')
        await interaction.response.send_message(embed=error_embed)

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
        bot.logger.error(f'{interaction.user} tried to play radio station {station} in {voice_channel.name} on server {interaction.guild.name} but was not in a voice channel')
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
        
        bot.logger.info(f'{interaction.user} played radio station {station} in {voice_channel.name} on server {interaction.guild.name}')
        active_embed = discord.Embed(title='Success', description=f'✅ Playing {station} in {voice_channel.name}.', color=discord.Color.green())
        await interaction.response.send_message(embed=active_embed)
        
        # Wait until the audio finishes playing or until the user disconnects
        while vc.is_playing():
            await asyncio.sleep(1)

        # Disconnect the bot after the stream ends
        await vc.disconnect()
    except Exception as e:
        error_embed = discord.Embed(title='Error', description=f'❌ Failed to play the radio station: {str(e)}', color=discord.Color.red())
        bot.logger.error(f'Failed to play radio station {station} in {voice_channel.name} on server {interaction.guild.name}: {str(e)}')
        await interaction.response.send_message(embed=error_embed)

# DISCONNECT COMMAND

@tree.command(name='disconnect', description='Disconnects the bot from the voice channel.')
async def disconnect(interaction: discord.Interaction):
    # Get the bot's voice channel
    voice_channel = bot.voice_clients[0] if bot.voice_clients else None
    # Disconnect the bot from the voice channel
    try:
        await voice_channel.disconnect()
        bot.logger.info(f'{interaction.user} disconnected from {voice_channel.name} in {interaction.guild.name}')
        disconnect_embed = discord.Embed(title='Success', description='✅ Disconnected from the voice channel.', color=discord.Color.green())
        await interaction.response.send_message(embed=disconnect_embed)
    except Exception as e:
        error_embed = discord.Embed(title='Error', description=f'❌ Failed to disconnect: {str(e)}', color=discord.Color.red())
        bot.logger.error(f'Failed to disconnect from Voice Channel {voice_channel.name} in {interaction.guild.name}: {str(e)}')
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

        bot.logger.info(f'{interaction.user} generated AI response: {response_text} on server {interaction.guild.name}')
        embed = discord.Embed(title="AI Response", description=response_text, color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

    except Exception as e:
        exception_embed = discord.Embed(title='Error', description=f"⚠️ Error generating response: {str(e)}", color=discord.Color.red())
        bot.logger.error(f'Error generating AI response on server {interaction.guild.name} by {interaction.user.name}: {str(e)}')
        await interaction.followup.send(embed=exception_embed)

# ECONOMY COMMANDS

# DAYLY REWARDS COMMAND

# Idea:
# Make a command that give you a daily reward of 100 points
# If the user has Premium then give them 500 points
# If the user has a Streak then give them these points:
# 7 Days: 200 Points (750 Points if Premium)
# 14 Days: 500 Points (1250 Points if Premium)
# 30 Days: 1000 Points (2500 Points if Premium)
# 90 Days: 2000 Points (5000 Points if Premium)
# 180 Days: 5000 Points (10000 Points if Premium)
# 365 Days: 10000 Points (25000 Points if Premium)
# The Points are stored in a SQL database sorted like this:
# UserID | Points | Streak | LastCollected

@tree.command(name='daily', description='Collect your daily reward points')
async def daily(interaction: discord.Interaction):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        base_points = 100
        premium_multiplier = 5
        
        # Check premium status
        application_id = bot.application_id
        data = await bot.http.get_entitlements(application_id)
        is_premium = any(e["user_id"] == str(interaction.user.id) and e["sku_id"] == "1347585991975637132" for e in data)
        
        # Check existing user
        cursor.execute('SELECT * FROM user_points WHERE user_id = %s', (interaction.user.id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            points_earned = base_points * (premium_multiplier if is_premium else 1)
            cursor.execute(
                'INSERT INTO user_points (user_id, points, streak, last_collected) VALUES (%s, %s, %s, %s)',
                (interaction.user.id, points_earned, 1, now)
            )
            streak = 1
        else:
            current_points = user_data[1]
            streak = user_data[2]
            last_collected = user_data[3]
            
            if (now - last_collected).days > 1:
                streak = 1
            else:
                streak += 1
                
            # Calculate streak bonus
            bonus = {
                365: 10000,
                180: 5000,
                90: 2000,
                30: 1000,
                14: 500,
                7: 200
            }.get(next((k for k in [365, 180, 90, 30, 14, 7] if streak >= k), 0), 0)
            
            points_earned = (base_points + bonus) * (premium_multiplier if is_premium else 1)
            
            cursor.execute(
                'UPDATE user_points SET points = points + %s, streak = %s, last_collected = %s WHERE user_id = %s',
                (points_earned, streak, now, interaction.user.id)
            )
        
        conn.commit()
        
        embed = discord.Embed(
            title="Daily Reward Collected!",
            description=f"You earned {points_earned} points!\nCurrent streak: {streak} days",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        
    except Error as e:
        bot.logger.error(f"Database error: {e}")
        await interaction.response.send_message("Error processing daily reward. Please try again later.")
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# TRANSFER COMMAND

# Idea:
# Make a command that allows you to transfer points to another user
# The user can only transfer points to users that are in the same server or outside the server if they have the user ID
# The Transaction will have a fee of (random between 5 and 15 that changes everyday at 12PM UTC+1 Berlin/Paris)% of the amount transferred
# The user is notified about the fee
# The fee goes to the UserId: 1011702976555004007
# The user can only transfer points that they have
# The user is notified about the transaction in a private message
# The message is structured like this:
# You have transferred {amount} points to {user} with a fee of {fee} points
# The recipient is notified about the transaction in a private message
# The message is structured like this:
# You have received {amount} points from {user}

@tree.command(name='transfer', description='Transfer points to another user')
async def transfer(interaction: discord.Interaction, recipient: discord.User, amount: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate fee (changes daily at 12PM UTC+1)
        now = datetime.now()
        seed = int(now.replace(hour=12, minute=0, second=0, microsecond=0).timestamp())
        random.seed(seed)
        fee_percentage = random.randint(5, 15)
        fee_amount = int(amount * (fee_percentage / 100))
        total_cost = amount + fee_amount

        # Get sender's points
        cursor.execute('SELECT points FROM user_points WHERE user_id = %s', (interaction.user.id,))
        sender_data = cursor.fetchone()

        if not sender_data or sender_data[0] < total_cost:
            await interaction.response.send_message(f"You need {total_cost} points for this transfer (including {fee_percentage}% fee)!")
            return

        # Update sender's points (deduct amount + fee)
        cursor.execute('UPDATE user_points SET points = points - %s WHERE user_id = %s', 
                      (total_cost, interaction.user.id))

        # Update or create recipient's points (gets full amount)
        cursor.execute('SELECT points FROM user_points WHERE user_id = %s', (recipient.id,))
        if cursor.fetchone():
            cursor.execute('UPDATE user_points SET points = points + %s WHERE user_id = %s',
                         (amount, recipient.id))
        else:
            cursor.execute('INSERT INTO user_points (user_id, points, streak, last_collected) VALUES (%s, %s, %s, %s)',
                         (recipient.id, amount, 0, now))

        # Add fee to specified user
        fee_user_id = 1011702976555004007
        cursor.execute('SELECT points FROM user_points WHERE user_id = %s', (fee_user_id,))
        if cursor.fetchone():
            cursor.execute('UPDATE user_points SET points = points + %s WHERE user_id = %s',
                         (fee_amount, fee_user_id))
        else:
            cursor.execute('INSERT INTO user_points (user_id, points, streak, last_collected) VALUES (%s, %s, %s, %s)',
                         (fee_user_id, fee_amount, 0, now))

        conn.commit()

        # Send confirmation messages
        sender_embed = discord.Embed(
            title="Transfer Successful",
            description=f"You transferred {amount} points to {recipient.name}\nFee paid: {fee_amount} points ({fee_percentage}%)\nTotal cost: {total_cost} points",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=sender_embed)

        # DM to recipient
        recipient_embed = discord.Embed(
            title="Points Received",
            description=f"You have received {amount} points from {interaction.user.name}",
            color=discord.Color.green()
        )
        try:
            await recipient.send(embed=recipient_embed)
        except discord.Forbidden:
            pass

        bot.logger.info(f'{interaction.user.name} transferred {amount} points to {recipient.name} with {fee_amount} points fee')

    except Error as e:
        bot.logger.error(f"Database error in transfer: {e}")
        error_embed = discord.Embed(
            title="Transfer Failed",
            description="An error occurred while processing the transfer.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=error_embed)

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# GAMBLE COMMAND

@tree.command(name='gamble', description='Gamble virtual points (Free to play for now!)')
async def gamble(interaction: discord.Interaction, bet_amount: int):
    # Generate random multiplier between 0.0 and 2.0
    multiplier = round(random.uniform(0, 2), 1)
    
    # Calculate winnings
    winnings = int(bet_amount * multiplier)
    
    # Create result message
    if multiplier > 1:
        color = discord.Color.green()
        bot.logger.info(f'{interaction.user} gambled {bet_amount} points with {multiplier}x multiplier and won in {interaction.guild.name}')
        result = f"🎉 You won {winnings} points!"
    elif multiplier == 1:
        color = discord.Color.yellow() 
        bot.logger.info(f'{interaction.user} gambled {bet_amount} points with {multiplier}x multiplier and broke even in {interaction.guild.name}')
        result = "🟡 You broke even!"
    else:
        color = discord.Color.red()
        bot.logger.info(f'{interaction.user} gambled {bet_amount} points with {multiplier}x multiplier and lost in {interaction.guild.name}')
        result = f"💸 You lost {bet_amount - winnings} points!"

    embed = discord.Embed(
        title="🎲 Gambling Results", 
        description=f"Bet Amount: {bet_amount}\nMultiplier: {multiplier}x\n{result}",
        color=color
    )
    
    await interaction.response.send_message(embed=embed)

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
    embed = discord.Embed(title='Credits', description='This bot was created by [SyncWide Solutions](<https://github.com/SyncWide-Solutions>)\n**Lead Developer:** [LolgamerHDDE](<https://github.com/LolgamerHDDE>)\n\n**Community Ideas:**\n**Ratte49:** /gamble Command', color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# LEGAL COMMAND

@tree.command(name='legal', description='Displays the bot legal information.')
async def legal(interaction: discord.Interaction):
    embed = discord.Embed(title='Nexus Legal Info', description=f'Here are the Legal Links for the bot {bot.user.name}:\n\nTerms Of Service (ToS): [Click Here](<https://syncwi.de/terms-of-service.html>)\nPrivacy Policy: [Click Here](<https://syncwi.de/privacy-policy.html>)\nContact: [Click Here](<https://syncwi.de/contact.html>)\n\n**Next Info only Relevant for Developers!**\n\nThe {bot.user.name} Bot is Licensed under the [MIT License](<https://opensource.org/license/mit>) which you can view by [Clicking Here](<https://github.com/SyncWide-Solutions/Nexus/blob/main/LICENSE>)', color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)

# This should be the 1000th line of code (goal).