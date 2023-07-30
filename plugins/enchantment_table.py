from typing import List, Optional
import asyncio

class EnchantmentTableBlock:
    def __init__(self, name):
        self.name = name

class EnchantmentTable:
    def __init__(self):
        self.type = "minecraft:enchant"
        self.slots = [None] * 3
        self.id = 0
        self.xpseed = -1
        self.enchantments = []
        self.on_close_callback = None

    def on(self, event, callback):
        if event == "close":
            self.on_close_callback = callback
        else:
            raise ValueError(f"Unsupported event: {event}")

    def emit(self, event):
        if event == "ready":
            pass
        else:
            raise ValueError(f"Unsupported event: {event}")

async def open_enchantment_table(bot, enchantment_table_block: EnchantmentTableBlock) -> EnchantmentTable:
    if enchantment_table_block.name != 'enchanting_table':
        raise ValueError('This is not an enchantment table')

    ready = False
    enchantment_table = EnchantmentTable()

    def reset_enchantment_options():
        enchantment_table.xpseed = -1
        enchantment_table.enchantments = []
        for _ in range(3):
            enchantment_table.enchantments.append({
                'level': -1,
                'expected': {
                    'enchant': -1,
                    'level': -1
                }
            })
        nonlocal ready
        ready = False

    def on_update_window_property(packet):
        if packet['windowId'] != enchantment_table.id:
            return

        assert packet['property'] >= 0
        slots = enchantment_table.enchantments

        if packet['property'] < 3:
            slot = slots[packet['property']]
            slot['level'] = packet['value']
        elif packet['property'] == 3:
            enchantment_table.xpseed = packet['value']
        elif packet['property'] < 7:
            slot = slots[packet['property'] - 4]
            slot['expected']['enchant'] = packet['value']
        elif packet['property'] < 10:
            slot = slots[packet['property'] - 7]
            slot['expected']['level'] = packet['value']

        if slots[0]['level'] >= 0 and slots[1]['level'] >= 0 and slots[2]['level'] >= 0:
            if not ready:
                nonlocal ready
                ready = True
                enchantment_table.emit('ready')
        else:
            nonlocal ready
            ready = False

    bot._client.on('craft_progress_bar', on_update_window_property)

    def on_close():
        bot._client.remove_listener('craft_progress_bar', on_update_window_property)
        if enchantment_table.on_close_callback:
            enchantment_table.on_close_callback()

    enchantment_table.on("close", on_close)

    reset_enchantment_options()

    async def enchant(choice):
        if not ready:
            await asyncio.wait_for(asyncio.Event().wait(), timeout=None)  # Wait indefinitely until ready
        choice = int(choice)  # allow string argument
        assert enchantment_table.enchantments[choice]['level'] != -1
        bot._client.write('enchant_item', {
            'windowId': enchantment_table.id,
            'enchantment': choice
        })

        def update_slot_predicate(old_item, new_item):
            return old_item is None and new_item is not None

        _, new_item = await asyncio.wait_for(asyncio.wait_for(bot.wait_for('updateSlot', predicate=update_slot_predicate), timeout=None), timeout=None)  # Wait indefinitely for updateSlot event
        return new_item

    async def take_target_item():
        item = enchantment_table.target_item()
        assert item
        await bot.put_away(item.slot)
        return item

    async def put_target_item(item):
        await bot.move_slot_item(item.slot, 0)

    async def put_lapis(item):
        await bot.move_slot_item(item.slot, 1)

    enchantment_table.enchant = enchant
    enchantment_table.take_target_item = take_target_item
    enchantment_table.put_target_item = put_target_item
    enchantment_table.put_lapis = put_lapis
    enchantment_table.target_item = lambda: enchantment_table.slots[0]

    return enchantment_table

def inject(bot):
    bot.open_enchantment_table = open_enchantment_table
