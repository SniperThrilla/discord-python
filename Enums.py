from enum import IntEnum

class ApplicationCommand(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNE = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11

class ButtonStyle(IntEnum):
    BLURPLE = 1
    GREY = 2
    GREEN = 3
    RED = 4
    GREY_URL = 5

class MenuType(IntEnum):
    STRING_SELECT = 3
    USER_SELECT = 5
    ROLE_SELECT = 6
    MENTIONABLE_SELECT = 7
    CHANNEL_SELECT = 8
