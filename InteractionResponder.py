# Allows users to easily create a response for an interaction.
import Message
import logging
import ApplicationCommands

from typing import (
    List
)

class Component():
    """
    The base class for all message components. The common features of message components such as their
    `custom_id` and their `message_callback` are stored here.

    """
    custom_id : str = None
    message_callback : ApplicationCommands.MessageComponentCallback = None
    client = None
    callback_function = None

    def __init__(self, custom_id, client, callback_function) -> None:
        """
        Creates a message component. This should not be called directly, as it purely is a parent
        class and will not generate meaningful JSON on its own.

        Parameters
        -------
        custom_id: `str`
            The custom identifier of this message component. In an interaction, this will be 
            provided to help you identify which message component has been interacted with.
        client: `Client.Client`
            A link back to the main client class. This allows the generation of custom identifiers.
        callback_function: `function`
            The function that will be run whenever this message component is interacted with. Works
            very similarly to the callback function for application commands in general. Your
            function **MUST** have the parameters client and interaction of type `Client.Client` and 
            `InteractionResponder.Interaction` respectively.

        Warning
        -------
        You should not ever directly create an instance of this class, but it can be used as the parent of other
        message components if you wish to make your own. See the `Button` class for an example of this.

        """
        self.client = client
        self.custom_id = client.generateCustomID(custom_id)
        self.callback_function = callback_function
        self.message_callback = ApplicationCommands.MessageComponentCallback(self.custom_id, self.callback_function)

    def generateJSON(self):
        """
        The parent class version of the function that all message components must have. This allows 
        components to generate the JSON necessary to provide in a HTTP POST to the API endpoint.

        Warning
        -------
        Without children, this function will not serve any purpose, hence the contents of this function.

        """
        pass

class Button(Component):
    """
    The button message component. Adding one of these to your response will add a clickable 
    button directly below your message.

    """

    label : str = None
    style : int = 1
    url : str = None
    
    def __init__(self, label, style, client, custom_id=None, url=None, callback=None) -> None:
        """
        Creates a button message component. 

        Parameters
        -------
        label: `str`
            The text that will be shown inside your button on the discord client.
        style: `int`
            Determines the colour (and functionality) of the button. Use `Enums.ButtonStyle`
            to see your options. Note that style 5 changes the button to a hyperlink and requires
            a URL to be set instead of a custom_id.
        client: `Client.Client`
            A link back to the main client class. This allows the generation of custom identifiers.
        custom_id: `str`
            The custom id of your button. This is provided whenever this button is pressed, and is used
            to identify that this button was pressed. It is randomised with a series of 20 characters,
            followed by _ and your custom_id. This is not important as the library already handles the 
            callback functions without this, but can be modified for more advanced control. This should
            not be set in addition to `url`.
        url: `str`
            The URL for style 5. This should not be set in addition to `custom_id`, and vice versa.
        callback: `function`
            The function that is triggered whenever a user presses the button. Your
            function **MUST** have the parameters client and interaction of type `Client.Client` and 
            `InteractionResponder.Interaction` respectively.

        """
        super().__init__(custom_id=custom_id, client=client, callback_function=callback)
        self.label = label
        self.style = style
        self.url = url


    def generateJSON(self) -> str:
        """
        Generates the JSON to be set in a HTTP request to the API endpoint for the button.

        Returns
        -------
        :class:`Dict[]`
            A dictionary representing the values to be translated into JSON.

        """
        #return '{"type": 2, "label": "' + self.label + '", "style": ' + str(self.style) + ', "custom_id": "' + self.custom_id + '"},'
        if self.style == 5:
            return {"type": 2, "label": self.label, "style": self.style, "url": self.url}
        return {"type": 2, "label": self.label, "style": self.style, "custom_id": self.custom_id}

class MenuOption():
    """
    The menu option component. This should be used with a SelectMenu of type 3, or STRING_SELECT. 
    This will not work in usage with any other types.

    """

    label : str = None
    value : str = None
    description : str = None
    default : bool = False

    def __init__(self, label, value, description, default=False) -> None:
        """
        Creates a select menu option component. 

        Parameters
        -------
        label: `str`
            The text that will be shown inside your option on the discord client.
        value: `str`
            The value that is returned to your application whenever this option is selected.
        description: `str`
            A description of your option that will appear on the discord client.
        default: `bool`
            Determines whether this option will be selected by default or not. Defaults to false.

        """
        self.label = label
        self.value = value
        self.description = description
        self.default = default

    def generateJSON(self):
        """
        Generates the JSON to be set in a HTTP request to the API endpoint for the menu option.

        Returns
        -------
        :class:`Dict[]`
            A dictionary representing the values to be translated into JSON.

        """
        return {"label": self.label, "value": self.value, "description": self.description, "default": self.default}

class SelectMenu(Component):
    """
    The select menu  component. This is a dropdown list that can be used with messages. Using a menu_type of STRING_SELECT
    or 3 will allow custom options. In this scenario, use in combination with a series of `MenuOption()`.

    """

    options : List[MenuOption] = []
    menu_type : int = 3
    placeholder : str = "Select option..."
    min_values : int = 1
    max_values : int = 1

    option_json = []

    def __init__(self, custom_id, client, menu_type : int = 3, placeholder = "Select option...", min_values : int = 1, max_values : int= 1, callback=None) -> None:
        """
        Creates a select menu  component. 

        Parameters
        -------
        custom_id: `str`
            The custom id of your menu. This is provided whenever this menu is used, and is used
            to identify that this menu was selected. It is randomised with a series of 20 characters,
            followed by _ and your custom_id. This is not important as the library already handles the 
            callback functions without this, but can be modified for more advanced control. 
        client: `Client.Client`
            A link back to the main client class. This allows the generation of custom identifiers.
        menu_type: `int`
            Determines what type of menu is created. Options are only enabled for type 3 or STRING_SELECT. 
            Use `Enums.MenuType` to see all options.
        placeholder: `str`
            The text that is shown by default before any option is selected. Defaults to `Select option...`
        min_values: `int`
            The minimum amount of options that can be selected. Defaults to 1.
        max_values: `int`
            The maximum amount of options that can be selected. Defaults to 1.
        callback: `function`
            The function that is triggered whenever a user presses the button. Your
            function **MUST** have the parameters client and interaction of type `Client.Client` and 
            `InteractionResponder.Interaction` respectively.

        """
        
        super().__init__(custom_id, client, callback)
        self.options = []
        self.option_json = []
        self.menu_type = menu_type
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values

    def addMenuOption(self, menu_option : MenuOption):
        """
        Generates the JSON to be set in a HTTP request to the API endpoint for the button.

        Parameters
        -------
        menu_option: `MenuOption`
            The MenuOption object to be added to the SelectMenu.

        Raises
        -------
        ValueError
            Raised if a MenuOption is added to a SelectMenu with an invalid type.

        Returns
        -------
        :class:`Dict[]`
            A dictionary representing the values to be translated into JSON.

        """

        if self.menu_type != 3:
            raise ValueError("Menu options are only available for STRING_SELECT menus (TYPE 3).")
        self.options.append(menu_option)
        self.option_json.append(menu_option.generateJSON())

    def generateJSON(self):
        """
        Generates the JSON to be set in a HTTP request to the API endpoint for the select menu.

        Returns
        -------
        :class:`Dict[]`
            A dictionary representing the values to be translated into JSON.

        """

        if self.menu_type == 3:
            return {"type": self.menu_type, "custom_id": self.custom_id, "options": self.option_json, 
            "placeholder": self.placeholder, "min_values": self.min_values, "max_values": self.max_values}
        return {"type": self.menu_type, "custom_id": self.custom_id, 
            "placeholder": self.placeholder, "min_values": self.min_values, "max_values": self.max_values}



class ActionRow():
    """
    ActionRows can hold other message components as folders. If you want to use
    a message component, then assign it to an ActionRow, and then assign an ActionRow
    to your Interaction Response.

    """

    components : List[Component] = []
    client = None

    def __init__(self, client) -> None:
        """
        Creates an ActionRow.

        Parameters
        -------
        client: `Client.Client`
            A link back to the main client class. This is used for adding callbacks to message
            components.

        Warning
        -------
        Message components do not have message callbacks unless they are inside an ActionRow. If,
        for some reason, you wish to have a component without an ActionRow, you must manually add
        the component's message_callback to the client's list of message_callbacks.

        """
        self.components = []
        self.client = client

    def addComponent(self, component):
        """
        Adds a message component to the ActionRow.

        Parameters
        -------
        component: `Component`
            The component that you want to assign to this ActionRow. This can also be
            any child class of the `Component` class, such as `Button` or `SelectMenu`.

        Warning
        -------
        Message components do not have message callbacks unless they are inside an ActionRow. If,
        for some reason, you wish to have a component without an ActionRow, you must manually add
        the component's message_callback to the client's list of message_callbacks.

        """

        self.components.append(component)
        self.client.message_callbacks.append(component.message_callback)

    def generateJSON(self) -> str:
        """
        Generates the JSON to be set in a HTTP request to the API endpoint for the action row.

        Returns
        -------
        :class:`Dict[]`
            A dictionary representing the values to be translated into JSON.

        """

        subComponents = []
        for component in self.components:
            subComponents.append(component.generateJSON())
        json = {"type": 1, "components": subComponents}

        return json

class Interaction:
    """
    The Interaction holds all of the important information your application could use when responding
    to an interaction. An Interaction object will be passed to your callback function which will 
    provide the necessary information for you to respond to an Interaction.

    """
    interaction_id = None
    interaction_token = None
    bot_token = None
    options = []

    def __init__(self, interaction_id, interaction_token, bot_token, options=[]) -> None:
        """
        Creates an interaction object. This should not be manually called, as it provides no functionality
        other than for providing Interaction information to callback functions.

        Parameters
        -------
        interaction_id: `str`
            The indentifier for the interaction. This is necessary for responding to an Interaction and is 
            provided by discord when an interaction is received.
        interaction_token: `str`
            Similar to the interaction_id, the interaction_token is necessary for responding to an Interaction and is 
            provided by discord when an interaction is received.
        bot_token: `str`
            This is the token by which your bot will authenticate its requests. This is taken from the `Client.Client`
            instance.
        options: `List[Dict[]]`
            The values returned from the parameters of a command. This is optional and will not always be present. If you
            have a required parameter in your command, this should be populated.
        

        """
        self.interaction_id = interaction_id
        self.interaction_token = interaction_token
        self.bot_token = bot_token
        self.options = options

class InteractionResponse:
    """
    The parent class for responses to Interactions. This on its own will not create a response and should not be directly implemented.
    Others classes such as InteractionResponseText inherits from this class.

    """
    ephemeral : bool = False
    url : str = None
    interaction : Interaction = None   
    json = None

    def __init__(self, interaction: Interaction, ephemeral=False) -> None:
        """
        Creates an interaction response. This is used for creating a `Message` which can be added to the interaction queue.

        Parameters
        -------
        interaction: `Interaction`
            The interaction object provides the necessary information to respond to the interaction.
        ephemeral: `bool`
            Whether the response will be visible to other members (False) or only visible to the user
            who triggered the interaction (True).

        """
        self.ephemeral = ephemeral
        self.interaction = interaction
        self.url = f"https://discord.com/api/v10/interactions/{interaction.interaction_id}/{interaction.interaction_token}/callback"

class InteractionResponseText(InteractionResponse):
    """
    Allows your application to respond to Interactions with a message containing text. This can be furthered by providing message 
    components to provide further functionality such as buttons and select menus. This is can be inputted into a `Message` and 
    then added to the message queue to be sent to the discord API endpoint.

    """

    components : List[Component] = []
    action_rows : List[ActionRow] = []
    text : str = None
    flag : int = 0

    def __init__(self, interaction: Interaction, text : str, ephemeral=False) -> None:
        """
        Creates an InteractionResponseText, which allows you to respond to an Interaction with a message,
        and additionally, a variety of message components to provide further functionality.

        Parameters
        -------
        interaction: `Interaction`
            The interaction object provides the necessary information to respond to the interaction.
        text: `str`
            The base message that will be sent in the response.
        ephemeral: `bool`
            Whether the response will be visible to other members (False) or only visible to the user
            who triggered the interaction (True).

        """
        super().__init__(interaction=interaction, ephemeral=ephemeral)

        self.text = text
        self.action_rows = []
        self.components = []

        flag = 0
        if ephemeral:
            flag += 1 << 6

        self.flag = flag

        self.json = {
            "type": Message.InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": text,
                "flags": flag
            }
        }

    def addComponent(self, component : Component):
        """
        Adds a message component to the response. In almost every case, components should 
        be added through ActionRows and this function should not be called.

        Parameters
        -------
        component: `Component`
            The component that you want to assign to this response. This can also be
            any child class of the `Component` class, such as `Button` or `SelectMenu`,
            although most message components must be within an ActionRow.

        Warning
        -------
        Message components do not have message callbacks unless they are inside an ActionRow. If,
        for some reason, you wish to have a component without an ActionRow, you must manually add
        the component's message_callback to the client's list of message_callbacks.

        """
        self.components.append(component)
        self.generateJSON()
        
    def addActionRow(self, action_row : ActionRow):
        """
        Adds an action row to the response. If you want to add components, you should
        add them to an ActionRow, as most of them require that, and the ActionRow class
        handles the callback functionality automatically.

        Parameters
        -------
        action_row: `ActionRow`
            The actionRow that you want to assign to this response. This ActionRow
            can have components attached to it.

        Warning
        -------
        Using ActionRows incorrectly can result in an error from discord. Check the
        Discord Developer Portal for documentation on the limits for usage. An example 
        of this is that you cannot have more than 5 ActionRows on a message.

        """
        self.action_rows.append(action_row)
        self.generateJSON()

    def generateJSON(self):
        """
        Generates the JSON to be set in a HTTP request to the API endpoint for the action row.
        Iterates through every component directly on this InteractionResponseText and all 
        ActionRows and their children components. This should be called prior to using the 
        `self.json` value, as this causes it to be updated with all of your components 
        included, however this is automatically run when a Component or ActionRow are added.

        Warning
        -------
        This function must be called before attempting to get the JSON from this class.

        Returns
        -------
        :class:`Dict[]`
            A dictionary representing the values to be translated into JSON.

        """

        new_json = []
        if len(self.action_rows) != 0 or len(self.components) != 0:
            for action_row in self.action_rows:
                #print(action_row.generateJSON())
                new_json.append(action_row.generateJSON())
            for component in self.components:
                new_json.append(component.generateJSON())

        self.json = {
            "type": Message.InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": self.text,
                "flags": self.flag,
                "components": new_json
            }
        }
        #print(self.json)
        return self.json


