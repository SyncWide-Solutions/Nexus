# Nexus Discord Bot

Nexus is a powerful and feature-rich Discord bot designed to enhance server moderation, automate tasks, and provide useful commands for Discord communities.

## Features
- **Moderation Tools:** Kick, ban, unban, and timeout users with simple commands.
- **Anti-Spam System:** Automatically deletes messages containing banned words.
- **Live Presence Update:** Displays the number of servers the bot is currently in.
- **Ping Command:** Checks the bot's responsiveness.
- **Invite Generator:** Generates an invite link for adding the bot to other servers.
- **Credits Command:** Displays information about the developers of Nexus.

## Installation
### Prerequisites
Ensure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/)
- [discord.py library](https://pypi.org/project/discord.py/)
- [dotenv library](https://pypi.org/project/python-dotenv/)

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
   DISCORD_BOT_TOKEN=your_token_here
   OPENAI_API_KEY=your_api_key_here
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands
### General Commands
| Command  | Description |
|----------|-------------|
| `/ping` | Checks if the bot is online |
| `/invite` | Generates an invite link for the bot |
| `/credits` | Shows the bot developer information |
| `/help` | Displays a list of available commands |

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

## Contact
- **Developer:** [LolgamerHDDE](https://github.com/LolgamerHDDE)
- **Organization:** [SyncWide Solutions](https://github.com/SyncWide-Solutions)

---
Enjoy using Nexus! 🚀

