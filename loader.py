import minecraft_protocol as mc
from events import EventEmitter
from plugin_loader import plugin_loader
from version import supported_versions, tested_versions
from location import Location
from painting import Painting
from scoreboard import ScoreBoard
from bossbar import BossBar
from particle import Particle
from prismarine_registry import PrismarineRegistry

plugins = {
    'bed': None,  # Fill this with the appropriate Python implementation for each plugin
    'title': None,
    'block_actions': None,
    'blocks': None,
    'book': None,
    'boss_bar': None,
    'breath': None,
    'chat': None,
    'chest': None,
    'command_block': None,
    'craft': None,
    'creative': None,
    'digging': None,
    'enchantment_table': None,
    'entities': None,
    'experience': None,
    'explosion': None,
    'fishing': None,
    'furnace': None,
    'game': None,
    'health': None,
    'inventory': None,
    'kick': None,
    'physics': None,
    'place_block': None,
    'rain': None,
    'ray_trace': None,
    'resource_pack': None,
    'scoreboard': None,
    'team': None,
    'settings': None,
    'simple_inventory': None,
    'sound': None,
    'spawn_point': None,
    'tablist': None,
    'time': None,
    'villager': None,
    'anvil': None,
    'place_entity': None,
    'generic_place': None,
    'particle': None
}

def create_bot(options=None):
    if options is None:
        options = {}

    options['username'] = options.get('username', 'Player')
    options['version'] = options.get('version', False)
    options['plugins'] = options.get('plugins', {})
    options['hideErrors'] = options.get('hideErrors', False)
    options['logErrors'] = options.get('logErrors', True)
    options['loadInternalPlugins'] = options.get('loadInternalPlugins', True)
    options['client'] = options.get('client', None)
    options['brand'] = options.get('brand', 'vanilla')
    options['respawn'] = options.get('respawn', True)

    bot = EventEmitter()
    bot._client = options['client']
    bot.end = lambda reason: bot._client.end(reason) if bot._client else None

    if options['logErrors']:
        def on_error(err):
            if not options['hideErrors']:
                print(err)
        bot.on('error', on_error)

    plugin_loader(bot, options)

    internal_plugins = [plugin for key, plugin in plugins.items() if options['plugins'].get(key, True) or options['loadInternalPlugins']]
    external_plugins = [plugin for key, plugin in options['plugins'].items() if callable(plugin)]

    bot.loadPlugins(internal_plugins + external_plugins)

    if not bot._client:
        bot._client = mc.create_client(options)

    def on_connect():
        bot.emit('connect')

    def on_error(err):
        bot.emit('error', err)

    def on_end(reason):
        bot.emit('end', reason)

    bot._client.on('connect', on_connect)
    bot._client.on('error', on_error)
    bot._client.on('end', on_end)

    if not bot._client.wait_connect:
        next_()
    else:
        bot._client.once('connect_allowed', next_)

    def next_():
        bot.registry = PrismarineRegistry(bot._client.version)
        version = bot.registry.version

        if version.majorVersion not in supported_versions:
            raise Exception(f"Version {version.minecraftVersion} is not supported.")

        latest_tested_version = tested_versions[-1]
        latest_protocol_version = PrismarineRegistry(latest_tested_version).protocol_version

        if version.protocol_version > latest_protocol_version:
            raise Exception(f"Version {version.minecraft_version} is not supported. Latest supported version is {latest_tested_version}.")

        bot.protocolVersion = version.version
        bot.majorVersion = version.majorVersion
        bot.version = version.minecraftVersion
        options['version'] = version.minecraftVersion
        bot.support_feature = bot.registry.support_feature

        bot.emit('inject_allowed')

    return bot
