def inject(bot):
    def on_entity_metadata(packet):
        if not bot.entity or bot.entity.id != packet.get("entityId"):
            return

        metadata = packet.get("metadata")

        if metadata[1].get("key") == 1:
            if not metadata[1].get("value"):
                return
            bot.oxygen_level = round(metadata[1]["value"] / 15)
            bot.emit("breath")

        if metadata[0].get("key") == 1:
            if not metadata[0].get("value"):
                return
            bot.oxygen_level = round(metadata[0]["value"] / 15)
            bot.emit("breath")

    bot._client.on("entity_metadata", on_entity_metadata)
