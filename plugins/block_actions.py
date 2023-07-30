from vec3 import Vec3

def inject(bot):
    CARDINALS = {
        'north': Vec3(0, 0, -1),
        'south': Vec3(0, 0, 1),
        'west': Vec3(-1, 0, 0),
        'east': Vec3(1, 0, 0)
    }

    FACING_MAP = {
        'north': {'west': 'right', 'east': 'left'},
        'south': {'west': 'left', 'east': 'right'},
        'west': {'north': 'left', 'south': 'right'},
        'east': {'north': 'right', 'south': 'left'}
    }

    instruments, blocks = bot.registry.instruments, bot.registry.blocks

    open_count_by_pos = {}

    def parse_chest_metadata(chest_block):
        chest_types = ['single', 'right', 'left']

        if bot.support_feature('doesntHaveChestType'):
            facing = list(CARDINALS.keys())[chest_block.metadata - 2] if chest_block.metadata - 2 >= 0 else None
            return {'facing': facing}
        else:
            metadata = chest_block.metadata
            waterlogged = not bool(metadata & 1)
            chest_type = chest_types[(metadata >> 1) % 3]
            facing = list(CARDINALS.keys())[metadata // 6]
            return {'waterlogged': waterlogged, 'type': chest_type, 'facing': facing}

    def get_chest_type(chest_block):
        if bot.support_feature('doesntHaveChestType'):
            facing = parse_chest_metadata(chest_block)['facing']
            if not facing:
                return 'single'

            perpendicular_cardinals = list(FACING_MAP[facing].keys())
            for cardinal in perpendicular_cardinals:
                cardinal_offset = CARDINALS[cardinal]
                adjacent_block = bot.block_at(chest_block.position + cardinal_offset)
                if adjacent_block and adjacent_block.type == chest_block.type:
                    return FACING_MAP[cardinal][facing]

            return 'single'
        else:
            return parse_chest_metadata(chest_block)['type']

    def on_block_action(packet):
        pt = Vec3(packet.location.x, packet.location.y, packet.location.z)
        block = bot.block_at(pt)

        if block is None or not blocks[packet.blockId]:
            return

        block_name = blocks[packet.blockId].name

        if block_name == 'noteblock':
            bot.emit('noteHeard', block, instruments[packet.byte1], packet.byte2)
        elif block_name == 'note_block':
            bot.emit('noteHeard', block, instruments[block.metadata // 50], (block.metadata % 50) // 2)
        elif block_name == 'sticky_piston' or block_name == 'piston':
            bot.emit('pistonMove', block, packet.byte1, packet.byte2)
        else:
            block2 = None

            if block_name == 'chest' or block_name == 'trapped_chest':
                chest_type = get_chest_type(block)
                if chest_type == 'right':
                    index = list(FACING_MAP[parse_chest_metadata(block)['facing']].values()).index('left')
                    cardinal_block2 = list(FACING_MAP[parse_chest_metadata(block)['facing']].keys())[index]
                    block2_position = block.position + CARDINALS[cardinal_block2]
                    block2 = bot.block_at(block2_position)
                elif chest_type == 'left':
                    return

            if open_count_by_pos.get(block.position) != packet.byte2:
                bot.emit('chestLidMove', block, packet.byte2, block2)

                if packet.byte2 > 0:
                    open_count_by_pos[block.position] = packet.byte2
                else:
                    open_count_by_pos.pop(block.position, None)

    def on_block_break_animation(packet):
        destroy_stage = packet.destroyStage
        pt = Vec3(packet.location.x, packet.location.y, packet.location.z)
        block = bot.block_at(pt)
        entity = bot.entities[packet.entityId] if packet.entityId in bot.entities else None

        if destroy_stage < 0 or destroy_stage > 9:
            bot.emit('blockBreakProgressEnd', block, entity)
        else:
            bot.emit('blockBreakProgressObserved', block, destroy_stage, entity)

    bot._client.on('block_action', on_block_action)
    bot._client.on('block_break_animation', on_block_break_animation)
