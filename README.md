# Nexus Discord Bot

Nexus is a powerful and feature-rich Discord bot designed to enhance server moderation, automate tasks, and provide useful commands for Discord communities.

## Features
- **Moderation Tools:** Kick, ban, unban, and timeout users with simple commands.
- **Anti-Spam System:** Automatically deletes messages containing banned words.
- **Live Presence Update:** Displays the number of servers the bot is currently in.
- **Ping Command:** Checks the bot's responsiveness.
- **Invite Generator:** Generates an invite link for adding the bot to other servers.
- **Credits Command:** Displays information about the developers of Nexus.
- **Logging**: Logs all actions performed by Nexus (bans, timeouts, etc.).

## Installation
### Prerequisites
Ensure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/SyncWide-Solutions/Nexus.git
   cd Nexus
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token
   OPENAI_API_KEY=your_openai_api_key
   UPTIME_KUMA_PASSWORD=your_uptime_kuma_password
   UPTIME_KUMA_URL=your_uptime_kuma_url
   UPTIME_KUMA_USERNAME=your_uptime_kuma_username
   FILTER=TRUE/FALSE
   DB_HOST=your_db_host
   DB_USERNAME=your_db_username
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   ```
4. Run the bot:
   ```bash
   python main.py
   ```

## Commands
### General Commands
| Command  | Description |
|----------|-------------|
| `/ping` | Checks if the bot is online |
| `/status` | Shows the current status of every SyncWide Solutions Server |
| `/invite` | Generates an invite link for the bot |
| `/credits` | Shows the bot developer information |
| `/help` | Displays a list of available commands |
| `/legal` | Displays the Bots Legal Information |
| `/version` | Shows the current version of the bot |
| `/8ball` | Ask a question to the 8ball |
| `/coinflip` | Flip a coin |

### Moderation Commands
| Command  | Description |
|----------|-------------|
| `/kick @user [reason]` | Kicks a user from the server |
| `/ban @user [reason]` | Bans a user from the server |
| `/unban @user` | Unbans a previously banned user |
| `/timeout @user [duration] [reason]` | Temporarily mutes a user |

### Premium Commands
| Command  | Description |
|----------|-------------|
| `/check` | Check your premium status |
| `/ai [prompt]` | Give a prompt to the AI |
| `/radio [station]` | Play a radio station |
| `/disconnect` | Disconnect from the Voice Channel |

### Costumization Commands
| Command  | Description |
|----------|-------------|
| `/nuke [messages]` | Deletes all channels channel |
| `/embed [title] [description] [color] [timestamp]` | Creates a costumizable Embed |
| `/serverinfo` | Shows the server information |
| `/setwelcome [channel] [message]` | Set the welcome message |
| `/stick [message]` | Stick a message to the top of the channel |
| `/unstick` | Unstick a message |

### Economic Commands
| Command  | Description |
|----------|-------------|
| `/balance` | Check your balance |
| `/transfer @user [amount]` | Transfer money to another user (with a fee) |
| `/gamble [amount]` | Gamble money |
| `/work` | Work for money |
| `/leaderboard` | Shows the leaderboard |
| `/daily` | Get your daily money |

## Configuration
Nexus includes a `banned_words.json` file where you can define words to be automatically removed from messages.
Modify `banned_words.json` to include additional words:
```json
{
    "banned_words": ["badword1", "badword2"]
}
```

## Contributing
Contributions are welcome! Feel free to fork this repository and submit pull requests.

## License
This project is licensed under the MIT License.

## Credits
- **Organization:** [SyncWide Solutions](https://github.com/SyncWide-Solutions)
- **Lead-Developer:** [LolgamerHDDE](https://github.com/LolgamerHDDE)

- **/gable Command:** @Ratte49

---
Enjoy using Nexus! 🚀

