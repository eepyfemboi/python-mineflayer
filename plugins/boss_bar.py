def inject(bot, version):
    BossBar = require('../bossbar')(bot.registry)
    bars = {}

    def on_boss_bar(packet):
        nonlocal bars

        if packet["action"] == 0:
            bars[packet["entityUUID"]] = BossBar(
                packet["entityUUID"],
                packet["title"],
                packet["health"],
                packet["dividers"],
                packet["color"],
                packet["flags"]
            )
            bot.emit("bossBarCreated", bars[packet["entityUUID"]])
        elif packet["action"] == 1:
            bot.emit("bossBarDeleted", bars[packet["entityUUID"]])
            bars.pop(packet["entityUUID"], None)
        else:
            if packet["entityUUID"] not in bars:
                return

            if packet["action"] == 2:
                bars[packet["entityUUID"]].health = packet["health"]

            if packet["action"] == 3:
                bars[packet["entityUUID"]].title = packet["title"]

            if packet["action"] == 4:
                bars[packet["entityUUID"]].dividers = packet["dividers"]
                bars[packet["entityUUID"]].color = packet["color"]

            if packet["action"] == 5:
                bars[packet["entityUUID"]].flags = packet["flags"]

            bot.emit("bossBarUpdated", bars[packet["entityUUID"]])

    bot._client.on("boss_bar", on_boss_bar)

    def get_boss_bars():
        return list(bars.values())

    bot.boss_bars = get_boss_bars
