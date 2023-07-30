import re
import asyncio

USERNAME_REGEX = r'(?:\(.{1,15}\)|\[.{1,15}\]|.){0,5}?(\w+)'
LEGACY_VANILLA_CHAT_REGEX = re.compile(f'^{USERNAME_REGEX}\\s?[>:\\-»\\]\\)~]+\\s(.*)$')

def inject(bot, options):
    CHAT_LENGTH_LIMIT = options.get('chatLengthLimit', 100) if bot.support_feature('lessCharsInChat') else 256
    defaultChatPatterns = options.get('defaultChatPatterns', True)

    def addDefaultPatterns():
        if not defaultChatPatterns:
            return

        # 1.19 changes the chat format to move <sender> prefix from message contents to a separate field.
        # TODO: new chat listener to handle this
        bot.add_chat_pattern('whisper', re.compile(f'^{USERNAME_REGEX} whispers(?: to you)?:? (.*)$'), deprecated=True)
        bot.add_chat_pattern('whisper', re.compile(f'^\\[{USERNAME_REGEX} -> \\w+\\s?\\] (.*)$'), deprecated=True)
        bot.add_chat_pattern('chat', LEGACY_VANILLA_CHAT_REGEX, deprecated=True)

    async def await_message(*args):
        resolve_messages = [x for x in args]
        def message_listener(msg):
            for x in resolve_messages:
                if isinstance(x, re.Pattern):
                    if x.match(msg):
                        resolve(msg)
                        bot.remove_listener('messagestr', message_listener)
                        break
                elif msg == x:
                    resolve(msg)
                    bot.remove_listener('messagestr', message_listener)
                    break
        bot.add_listener('messagestr', message_listener)

    def chat_with_header(header, message):
        if isinstance(message, int):
            message = str(message)
        if not isinstance(message, str):
            raise ValueError('Incorrect type! Should be a string or number.')

        if bot.support_feature('signedChat') and message.startswith('/'):
            # We send commands as Chat Command packet in 1.19+
            command = message[1:]
            timestamp = int((datetime.utcnow() - datetime(2000, 1, 1)).total_seconds() * 1000)
            bot._client.write('chat_command', {
                'command': command,
                'timestamp': timestamp,
                'salt': 0,
                'argumentSignatures': [],
                'signedPreview': False,
                'messageCount': 0,
                'acknowledged': b'\x00\x00\x00',
                # 1.19.2 Chat Command packet also includes an array of last seen messages
                'previousMessages': []
            })
            return

        length_limit = CHAT_LENGTH_LIMIT - len(header)
        for sub_message in message.split('\n'):
            if not sub_message:
                continue
            for i in range(0, len(sub_message), length_limit):
                small_msg = header + sub_message[i:i + length_limit]
                bot._client.chat(small_msg)

    async def tab_complete(text, assume_command=False, send_block_in_sight=True):
        position = None

        if send_block_in_sight:
            block = bot.block_at_cursor()

            if block:
                position = block.position

        bot._client.write('tab_complete', {
            'text': text,
            'assumeCommand': assume_command,
            'lookedAtBlock': position
        })

        packet = await asyncio.wait_for(bot.wait_for('tab_complete'), timeout=5)
        return packet.get('matches', [])

    def whisper(username, message):
        chat_with_header(f'/tell {username} ', message)

    def chat(message):
        chat_with_header('', message)

    bot.add_chat_pattern_set = lambda name, patterns, opts=None: None
    bot.add_chat_pattern = lambda name, pattern, opts=None: None
    bot.remove_chat_pattern = lambda name: None

    bot.whisper = whisper
    bot.chat = chat
    bot.tab_complete = tab_complete
    bot.await_message = await_message

    addDefaultPatterns()

    bot.add_listener('player_chat', on_player_chat)
    bot.add_listener('system_chat', on_system_chat)

def on_player_chat(data):
    message = data['formattedMessage']
    verified = data['verified']
    if bot.support_feature('clientsideChatFormatting'):
        parameters = {
            'sender': json.loads(data.get('senderName', '{}')),
            'target': json.loads(data.get('targetName', '{}')),
            'content': json.loads(message) if message else {'text': data['plainMessage']}
        }
        msg = ChatMessage.from_network(data['type'], parameters)
        if data['unsignedContent']:
            msg.unsigned = ChatMessage.from_network(data['type'], {
                'sender': parameters['sender'],
                'target': parameters['target'],
                'content': json.loads(data['unsignedContent'])
            })
    else:
        msg = ChatMessage.from_notch(message)
    bot.emit('message', msg, 'chat', data['sender'], verified)
    bot.emit('messagestr', msg.to_string(), 'chat', msg, data['sender'], verified)

def on_system_chat(data):
    msg = ChatMessage.from_notch(data['formattedMessage'])
    chat_positions = {1: 'system', 2: 'game_info'}
    bot.emit('message', msg, chat_positions[data['positionId']], None)
    bot.emit('messagestr', msg.to_string(), chat_positions[data['positionId']], msg, None)
    if data['positionId'] == 2:
        bot.emit('actionBar', msg, None)
