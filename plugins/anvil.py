import assert
from promise_utils import sleep
from events import once

def inject(bot):
    from prismarine_item import Item

    def match_window_type(window):
        return "minecraft:(?:chipped_|damaged_)?anvil" in window.type

    async def open_anvil(anvil_block):
        anvil = await bot.open_block(anvil_block)
        if not match_window_type(anvil):
            raise Exception('This is not an anvil-like window')

        def err(name):
            anvil.close()
            raise Exception(name)

        def send_item_name(name):
            if bot.support_feature('useMCItemName'):
                bot._client.write_channel('MC|ItemName', name)
            else:
                bot._client.write('name_item', {'name': name})

        async def add_custom_name(name):
            if not name:
                return
            for i in range(1, len(name) + 1):
                send_item_name(name[:i])
                await sleep(50)

        async def put_in_anvil(item_one, item_two):
            await put_something(0, item_one.type, item_one.metadata, item_one.count, item_one.nbt)
            send_item_name('')  # sent like this by vanilla
            if not bot.support_feature('useMCItemName'):
                send_item_name('')
            await put_something(1, item_two.type, item_two.metadata, item_two.count, item_two.nbt)

        async def combine(item_one, item_two, name=None):
            if name and len(name) > 35:
                err('Name is too long.')
            if bot.support_feature('useMCItemName'):
                bot._client.register_channel('MC|ItemName', 'string')

            assert item_one and item_two
            normal_cost = Item.anvil(item_one, item_two, bot.game.game_mode == 'creative', name).xp_cost
            inverse_cost = Item.anvil(item_two, item_one, bot.game.game_mode == 'creative', name).xp_cost
            if normal_cost == 0 and inverse_cost == 0:
                err('Not anvil-able (in either direction), cancelling.')

            smallest = min(normal_cost, inverse_cost) if normal_cost < inverse_cost else inverse_cost
            if bot.game.game_mode != 'creative' and bot.experience.level < smallest:
                err('Player does not have enough xp to do action, cancelling.')

            xp_promise = bot.game.game_mode == 'creative' and Promise.resolve() or once(bot, 'experience')
            if normal_cost == 0:
                await put_in_anvil(item_two, item_one)
            elif inverse_cost == 0:
                await put_in_anvil(item_one, item_two)
            elif normal_cost < inverse_cost:
                await put_in_anvil(item_one, item_two)
            else:
                await put_in_anvil(item_two, item_one)

            await add_custom_name(name)
            await bot.put_away(2)
            await xp_promise

        async def rename(item, name=None):
            if name and len(name) > 35:
                err('Name is too long.')
            if bot.support_feature('useMCItemName'):
                bot._client.register_channel('MC|ItemName', 'string')
            assert item
            normal_cost = Item.anvil(item, None, bot.game.game_mode == 'creative', name).xp_cost
            if normal_cost == 0:
                err('Not valid rename, cancelling.')

            if bot.game.game_mode != 'creative' and bot.experience.level < normal_cost:
                err('Player does not have enough xp to do action, cancelling.')
            xp_promise = once(bot, 'experience')
            await put_something(0, item.type, item.metadata, item.count, item.nbt)
            send_item_name('')  # sent like this by vanilla
            if not bot.support_feature('useMCItemName'):
                send_item_name('')
            await add_custom_name(name)
            await bot.put_away(2)
            await xp_promise

        async def put_something(dest_slot, item_id, metadata, count, nbt):
            options = {
                'window': anvil,
                'itemType': item_id,
                'metadata': metadata,
                'count': count,
                'nbt': nbt,
                'sourceStart': anvil.inventory_start,
                'sourceEnd': anvil.inventory_end,
                'destStart': dest_slot,
                'destEnd': dest_slot + 1
            }
            await bot.transfer(options)

        anvil.combine = combine
        anvil.rename = rename

        return anvil

    bot.open_anvil = open_anvil
