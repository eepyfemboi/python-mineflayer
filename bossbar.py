from enum import Enum
import json

class ChatMessage:
    def __init__(self, message):
        self.message = message

class Color(Enum):
    PINK = 'pink'
    BLUE = 'blue'
    RED = 'red'
    GREEN = 'green'
    YELLOW = 'yellow'
    PURPLE = 'purple'
    WHITE = 'white'

class Divisions(Enum):
    DIV_0 = 0
    DIV_6 = 6
    DIV_10 = 10
    DIV_12 = 12
    DIV_20 = 20

def loader(registry):
    return BossBar

class BossBar:
    def __init__(self, uuid, title, health, dividers, color, flags):
        self._entityUUID = uuid
        self._title = ChatMessage(json.loads(title))
        self._health = health
        self._dividers = Divisions(dividers)
        self._color = Color(color)
        self._shouldDarkenSky = bool(flags & 0x1)
        self._isDragonBar = bool(flags & 0x2)
        self._createFog = bool(flags & 0x4)

    @property
    def entityUUID(self):
        return self._entityUUID

    @entityUUID.setter
    def entityUUID(self, uuid):
        self._entityUUID = uuid

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = ChatMessage(json.loads(title))

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, health):
        self._health = health

    @property
    def dividers(self):
        return self._dividers

    @dividers.setter
    def dividers(self, dividers):
        self._dividers = Divisions(dividers)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = Color(color)

    @property
    def flags(self):
        return (self._shouldDarkenSky) | (self._isDragonBar << 1) | (self._createFog << 2)

    @flags.setter
    def flags(self, flags):
        self._shouldDarkenSky = bool(flags & 0x1)
        self._isDragonBar = bool(flags & 0x2)
        self._createFog = bool(flags & 0x4)

    @property
    def shouldDarkenSky(self):
        return self._shouldDarkenSky

    @shouldDarkenSky.setter
    def shouldDarkenSky(self, darkenSky):
        self._shouldDarkenSky = darkenSky

    @property
    def isDragonBar(self):
        return self._isDragonBar

    @isDragonBar.setter
    def isDragonBar(self, dragonBar):
        self._isDragonBar = dragonBar

    @property
    def createFog(self):
        return self._createFog

    @createFog.setter
    def createFog(self, createFog):
        self._createFog = createFog
