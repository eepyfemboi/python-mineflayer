from prismarine_chat import ChatMessage

def sort_items(item):
    return -item['value']

class ScoreBoard:
    def __init__(self, packet):
        self.name = packet['name']
        self.set_title(packet['displayText'])
        self.items_map = {}

    def set_title(self, title):
        try:
            self.title = ChatMessage.from_json(title).to_plain_text()  # version>1.13
        except:
            self.title = title

    def add(self, name, value):
        self.items_map[name] = {
            'name': name,
            'value': value,
            'displayName': bot.team_map[name].display_name(name) if name in bot.team_map else ChatMessage(name)
        }
        return self.items_map[name]

    def remove(self, name):
        removed = self.items_map.get(name)
        if removed is not None:
            del self.items_map[name]
        return removed

    @property
    def items(self):
        return sorted(list(self.items_map.values()), key=sort_items)

class ScoreBoardPositions:
    @property
    def list(self):
        return 0

    @property
    def sidebar(self):
        return 1

    @property
    def belowName(self):
        return 2

ScoreBoard.positions = ScoreBoardPositions()

# Assuming `bot` is a valid instance of your bot class, and `bot.team_map` contains the team information.
# Make sure to define `bot.team_map` before creating the `ScoreBoard` instances.

# Example usage:
# packet = {
#     'name': 'scoreboard_name',
#     'displayText': '{"text": "My Scoreboard"}'  # JSON representation for 1.13 and above, plain text for older versions
# }
# scoreboard = ScoreBoard(packet)
# scoreboard.add('player1', 100)
# scoreboard.add('player2', 150)
# scoreboard.remove('player1')
# for item in scoreboard.items:
#     print(item['name'], item['value'])

# scoreboard_position = ScoreBoard.positions.sidebar
# print(scoreboard_position)

# Make sure to adjust your code accordingly to handle actual bot instances and team data.

