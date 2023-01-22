# Registers application commands and syncs them.
import aiohttp
import asyncio

from typing import (
    List
)

class ApplicationCommandChoice():

    name: str = None
    value : str = None

    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value

    def generateJSON(self):
        return {"name": self.name, "value": self.value}

class ApplicationCommandOption():

    type : int = 3
    name : str = None
    description : str = None
    required : bool = False
    choices : List[ApplicationCommandChoice] = []

    def __init__(self, type, name, description, required=False) -> None:
        self.choices = []
        self.type = type
        self.name = name
        self.description = description
        self.required = required

    def addChoice(self, choice : ApplicationCommandChoice):
        self.choices.append(choice)

    def generateJSON(self):
        json = []
        for choice in self.choices:
            json.append(choice.generateJSON())
        if json == []:
            return {"name": self.name, "description": self.description, "type": self.type, "required": self.required}
        return {"name": self.name, "description": self.description, "type": self.type, "required": self.required, "choices": json}

class ApplicationCommand():
    
    name : str = None
    type : int = None
    description : str = None
    function = None
    options : List[ApplicationCommandOption] = []

    def __init__(self, name : str, type : int, description : str, function, options : List[ApplicationCommandOption] = []) -> None:
        self.name = name
        self.type = type
        self.description = description
        self.function = function
        self.options = options

    def generateJSON(self):
        json = []
        for option in self.options:
            json.append(option.generateJSON())
        return json

class MessageComponentCallback():

    custom_id : str = None
    function = None

    def __init__(self, custom_id : str, function) -> None:
        self.custom_id = custom_id
        self.function = function