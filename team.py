from prismarine_chat import ChatMessage, MessageBuilder

def color_string(color):
    formatting = [
        'black', 'dark_blue', 'dark_green', 'dark_aqua', 'dark_red', 'dark_purple', 'gold', 'gray',
        'dark_gray', 'blue', 'green', 'aqua', 'red', 'light_purple', 'yellow', 'white', 'obfuscated',
        'bold', 'strikethrough', 'underlined', 'italic', 'reset'
    ]
    if color is None or color > 21 or color == -1:
        return 'reset'
    return formatting[color]

class Team:
    def __init__(self, team, name, friendlyFire, nameTagVisibility, collisionRule, formatting, prefix, suffix):
        self.team = team
        self.update(name, friendlyFire, nameTagVisibility, collisionRule, formatting, prefix, suffix)
        self.membersMap = {}

    def parse_message(self, value):
        try:
            result = ChatMessage.from_json(value)  # version>1.13-pre7
        except:
            result = MessageBuilder.from_string(value, color_separator='§')
            if result is None:
                return ChatMessage('')
            return ChatMessage.from_json(result.to_json())
        return result

    def add(self, name):
        self.membersMap[name] = ''
        return self.membersMap[name]

    def remove(self, name):
        removed = self.membersMap.get(name)
        if removed is not None:
            del self.membersMap[name]
        return removed

    def update(self, name, friendlyFire, nameTagVisibility, collisionRule, formatting, prefix, suffix):
        self.name = self.parse_message(name)
        self.friendlyFire = friendlyFire
        self.nameTagVisibility = nameTagVisibility
        self.collisionRule = collisionRule
        self.color = color_string(formatting)
        self.prefix = self.parse_message(prefix)
        self.suffix = self.parse_message(suffix)

    # Return a chat component with prefix + color + name + suffix
    def display_name(self, member):
        name = self.prefix.clone()
        name.append(ChatMessage(text=member, color=self.color), self.suffix)
        return name

    @property
    def members(self):
        return list(self.membersMap.keys())
