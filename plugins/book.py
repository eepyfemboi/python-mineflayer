import asyncio
import re

def inject(bot):
    Item = bot.registry["prismarine-item"]

    if bot.support_feature("editBookIsPluginChannel"):
        bot._client.registerChannel("MC|BEdit", "slot")
        bot._client.registerChannel("MC|BSign", "slot")

        def edit_book(book, signing=False):
            if signing:
                bot._client.writeChannel("MC|BSign", Item.to_notch(book))
            else:
                bot._client.writeChannel("MC|BEdit", Item.to_notch(book))

    elif bot.support_feature("hasEditBookPacket"):

        def edit_book(book, signing=False, hand=0):
            bot._client.write("edit_book", {
                "new_book": Item.to_notch(book),
                "signing": signing,
                "hand": hand
            })

    async def write(slot, pages, author, title, signing):
        assert 0 <= slot <= 44, "slot out of inventory range"
        book = bot.inventory.slots[slot]
        assert book and book.type == bot.registry.items_by_name["writable_book"].id, f"no book found in slot {slot}"
        quick_bar_slot = bot.quick_bar_slot
        move_to_quick_bar = slot < 36

        if move_to_quick_bar:
            await bot.move_slot_item(slot, 36)

        bot.set_quick_bar_slot(0 if move_to_quick_bar else slot - 36)

        modified_book = await modify_book(36 if move_to_quick_bar else slot, pages, author, title, signing)
        edit_book(modified_book, signing)
        await asyncio.wait_for(bot.inventory.wait_for_update(f"updateSlot:{36 if move_to_quick_bar else slot}"), timeout=5)

        bot.set_quick_bar_slot(quick_bar_slot)

        if move_to_quick_bar:
            await bot.move_slot_item(36, slot)

    def modify_book(slot, pages, author, title, signing):
        book = dict(bot.inventory.slots[slot])
        if "nbt" not in book or book["nbt"]["type"] != "compound":
            book["nbt"] = {
                "type": "compound",
                "name": "",
                "value": {}
            }
        if signing:
            if bot.support_feature("clientUpdateBookIdWhenSign"):
                book["type"] = bot.registry.items_by_name["written_book"].id
            book["nbt"]["value"]["author"] = {
                "type": "string",
                "value": author
            }
            book["nbt"]["value"]["title"] = {
                "type": "string",
                "value": title
            }
        book["nbt"]["value"]["pages"] = {
            "type": "list",
            "value": {
                "type": "string",
                "value": pages
            }
        }
        bot.inventory.update_slot(slot, book)
        return book

    async def write_book(slot, pages):
        await write(slot, pages, None, None, False)

    async def sign_book(slot, pages, author, title):
        await write(slot, pages, author, title, True)

    bot.write_book = write_book
    bot.sign_book = sign_book
