# discord-python
A discord API wrapper made for developing discord bots in python.

## Features
- Application Commands
- Message Components
- Modals
- Embeds
- Voice support
- Automatic Gateway Integration
- Low-level access to websockets

## Limitations
- Issues with reconnecting if disconnected.
- Lack of voice support
- Lack of other features.

## In Progress
- Rate limiting

## Installation

Install the package using pip, or by cloning this repository.
```
# Linux/macOS
python3 -m pip install -U discord_python_sniperthrilla

# Windows
py -3 -m pip install -U discord_python_sniperthrilla
```

Required packages
```
aiohttp
requests
```

## Usage

A simple bot with a /help slash command, which takes in a parameter and responds with text and a button.
```python
# Import relevant classes.
import discord_python as dp

# Create a client and add the commands.
client = dp.Client()

# For the /help command, the callback function is called help, but can be called anything.
# Instead of registering the commands with the registerApplicationCommand() function, you can use a decorator as follows.
@client.AppCommand(name="help", description="description", parameters = [dp.ApplicationCommandOption(dp.ApplicationCommandType.STRING, "name", "description", required=True)])
async def help(client : dp.Client, interaction : dp.Interaction):

    # Respond with a message saying, "Hello, World!"
    response = dp.InteractionResponseText(interaction=interaction, text="Hello, world!", ephemeral=True)
    
    # Create an action row.
    actionRow = dp.ActionRow(client=client)

    # Adds a button to the action row which is added to the message.
    actionRow.addComponent(dp.Button("Click me!", dp.ButtonStyle.BLURPLE, client, "customID", callback=callback_function_here))
    response.addActionRow(actionRow)
    response.generateJSON()
    
    # Send the message to discord!
    message = dp.Message(url=response.url, method=dp.HTTPMethods.POST, json=response.json, client=client)
    client.messageQueue.append(message)

client.syncApplicationCommands()
client.run("BOT TOKEN HERE")
```

A simple command for playing audio files or urls in a given voice channel.

```python
# Creates a command named voice with a channel parameter/
@client.AppCommand(name="voice", description="Play audio in a voice channel.", parameters=[dp.ApplicationCommandOption(dp.ApplicationCommandType.CHANNEL, "voice-channel", "The voice channel to join.", True)])
async def voice(client: dp.Client, interaction: dp.Interaction):
    # Responds to the command with a message
    response = dp.InteractionResponseText(interaction, "Responded.", True)
    message = dp.Message(url=response.url, method=dp.HTTPMethods.POST, json=response.json, client=client)
    client.messageQueue.append(message)

    # Gets the channel information of the provided channel
    channel = await client.getChannel(interaction.options[0]['value'])
    guild_id = channel['guild_id']

    # Creates a voice client (handles the creation of a new websocket and UDP connection)
    vc = await client.getVoiceClient(guild_id, interaction.options[0]['value'], False, False)

    # Plays a file or URL in the voice channel.
    await vc.play(dp.FFmpegOpus("file.mp3"))

```


## Contributing

Feel free to open an issue to discuss any changes.

## License

[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
