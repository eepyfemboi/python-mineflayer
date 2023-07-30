from vec3 import Vec3

def inject(bot):
    allowed_window_types = ['minecraft:generic', 'minecraft:chest', 'minecraft:dispenser', 'minecraft:ender_chest',
                            'minecraft:shulker_box', 'minecraft:hopper', 'minecraft:container', 'minecraft:dropper',
                            'minecraft:trapped_chest', 'minecraft:barrel', 'minecraft:white_shulker_box',
                            'minecraft:orange_shulker_box', 'minecraft:magenta_shulker_box',
                            'minecraft:light_blue_shulker_box', 'minecraft:yellow_shulker_box',
                            'minecraft:lime_shulker_box', 'minecraft:pink_shulker_box', 'minecraft:gray_shulker_box',
                            'minecraft:light_gray_shulker_box', 'minecraft:cyan_shulker_box',
                            'minecraft:purple_shulker_box', 'minecraft:blue_shulker_box', 'minecraft:brown_shulker_box',
                            'minecraft:green_shulker_box', 'minecraft:red_shulker_box', 'minecraft:black_shulker_box']

    def match_window_type(window):
        for window_type in allowed_window_types:
            if window['type'].startswith(window_type):
                return True
        return False

    async def open_container(container_to_open, direction=None, cursor_pos=None):
        direction = direction if direction is not None else Vec3(0, 1, 0)
        cursor_pos = cursor_pos if cursor_pos is not None else Vec3(0.5, 0.5, 0.5)
        chest = None
        if isinstance(container_to_open, bot.block_class) and container_to_open.name in map(lambda x: x.replace('minecraft:', ''), allowed_window_types):
            chest = await bot.open_block(container_to_open, direction, cursor_pos)
        elif isinstance(container_to_open, bot.entity_class):
            chest = await bot.open_entity(container_to_open)
        else:
            raise ValueError('containerToOpen is neither a block nor an entity')

        if not match_window_type(chest):
            raise ValueError('Non-container window used as a container')
        return chest

    bot.open_container = open_container
    bot.open_chest = open_container
    bot.open_dispenser = open_container
