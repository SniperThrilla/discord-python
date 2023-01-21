# discord-python
A discord API wrapper made for developing discord bots in python.

## Installation
There is currently no package, so just grab the files and dump them in your directory.

## Usage

```python
# Create a client and add two commands.
client = Client.Client()

# Register a new application command /help with a string parameter called "test" and responds with the function "help"
client.registerApplicationCommand("help", Enums.ApplicationCommand.SUB_COMMAND, "my epic description", help, [ApplicationCommands.ApplicationCommandOption(3, "test", True)])

# Register another application command called /menu
client.registerApplicationCommand("menu", Enums.ApplicationCommand.SUB_COMMAND, "testing select menus", menu)

client.syncApplicationCommands()
client.run("BOT TOKEN HERE")
```

```python
# For the /help command, the callback function is called help, but can be called anything.
def help(client : Client.Client, interaction : InteractionResponder.Interaction):

    # Respond with a message saying, "Hello, World!"
    response = InteractionResponder.InteractionResponseText(interaction=interaction, text="Hello, world!", ephemeral=True)
    
    # Create an action row.
    actionRow = InteractionResponder.ActionRow(client=client)

    # Adds a button to the message with the option set by the user as the label
    actionRow.addComponent(InteractionResponder.Button(interaction.options[0]['value'], Enums.ButtonStyle.BLURPLE, client, "test1", callback=callback_test1))
    response.addActionRow(actionRow)
    response.generateJSON()
    
    # Send the message to discord!
    message = Message.Message(url=response.url, method=Message.HTTPMethods.POST, json=response.json, client=client)
    client.messageQueue.append(message)
```

## Contributing

Feel free to open an issue to discuss any changes.

## License

[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
