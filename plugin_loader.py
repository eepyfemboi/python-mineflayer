class PluginLoader:
    def __init__(self, bot, options):
        self.bot = bot
        self.options = options
        self.loaded = False
        self.plugin_list = []
        bot.once('inject_allowed', self.on_inject_allowed)

    def on_inject_allowed(self):
        self.loaded = True
        self.inject_plugins()

    def load_plugin(self, plugin):
        if not callable(plugin):
            raise ValueError('Plugin needs to be a function')

        if self.has_plugin(plugin):
            return

        self.plugin_list.append(plugin)

        if self.loaded:
            plugin(self.bot, self.options)

    def load_plugins(self, plugins):
        for plugin in plugins:
            if not callable(plugin):
                raise ValueError('Plugins need to be an array of functions')

            self.load_plugin(plugin)

    def inject_plugins(self):
        for plugin in self.plugin_list:
            plugin(self.bot, self.options)

    def has_plugin(self, plugin):
        return plugin in self.plugin_list

    def register_functions(self):
        self.bot.load_plugin = self.load_plugin
        self.bot.load_plugins = self.load_plugins
        self.bot.has_plugin = self.has_plugin
