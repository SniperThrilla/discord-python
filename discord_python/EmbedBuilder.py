# A simple method for adding embeds to your application.

from typing import (
    List
)

class Author():

    name : str = None
    url : str = None
    icon_url : str = None

    def __init__(self, name : str, url : str = None, icon_url : str = None) -> None:
        self.name = name
        self.url = url
        self.icon_url = icon_url

class Field():

    name : str = None
    value : str = None
    inline : bool = False

    def __init__(self, name : str, value : str, inline : bool = False) -> None:
        self.name = name
        self.value = value
        self.inline = inline

    def generateJSON(self):
        return {"name": self.name, "value": self.value, "inline": self.inline}

class Embed():

    title : str = None
    description : str = None
    color : int = 5918163
    url : str = None
    image : str = None
    thumbnail : str = None
    author : Author = None
    footer_text : str = None
    footer_icon : str = None
    
    fields : List[Field] = []


    def __init__(self, title : str, description: str, color : int = 5918163, url : str = None, image : str = None, thumbnail : str = None, author : Author = None, footer_text : str = None, footer_icon : str = None) -> None:
        self.title = title
        self.description = description
        self.color = color
        self.url = url
        self.image = image
        self.thumbnail = thumbnail
        self.author = author
        self.footer_text = footer_text
        self.footer_icon = footer_icon

        self.fields = []

    def addField(self, field : Field):
        self.fields.append(field)

    def generateJSON(self):
        
        field_json = []
        for field in self.fields:
            field_json.append(field.generateJSON())

        image_json = None
        if self.image != None:
            image_json = {"url": self.image}

        author_json = None
        if self.author != None:
            author_json = {"name": self.author.name, "url": self.author.url, "icon_url": self.author.icon_url}
        
        footer_json = None
        if self.author != None:
            footer_json = {"text": self.footer_text, "icon_url": self.footer_icon}

        return {
            "type": "rich",
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "fields": field_json,
            "image": image_json,
            "author": author_json,
            "footer": footer_json,
            "url": self.url,
        }
