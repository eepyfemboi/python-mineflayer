from vec3 import Vec3

def inject(bot):
    bot.is_sleeping = False

    beds = set(['white_bed', 'orange_bed', 'magenta_bed', 'light_blue_bed', 'yellow_bed', 'lime_bed', 'pink_bed', 'gray_bed',
                'light_gray_bed', 'cyan_bed', 'purple_bed', 'blue_bed', 'brown_bed', 'green_bed', 'red_bed', 'black_bed', 'bed'])

    def is_a_bed(block):
        return block.name in beds

    def parse_bed_metadata(bed_block):
        metadata = {
            'part': False,  # True: head, False: foot
            'occupied': 0,
            'facing': 0,  # 0: south, 1: west, 2: north, 3 east
            'head_offset': Vec3(0, 0, 1)
        }

        if bot.support_feature('blockStateId'):
            state = bed_block.state_id - bot.registry.blocks_by_state_id[bed_block.state_id].min_state_id
            bit_metadata = bin(state)[2:].zfill(4)  # FACING (first 2 bits), PART (3rd bit), OCCUPIED (4th bit)
            metadata['part'] = bit_metadata[3] == '0'
            metadata['occupied'] = bit_metadata[2] == '0'

            if bit_metadata[:2] == '00':
                metadata['facing'] = 2
                metadata['head_offset'] = Vec3(0, 0, -1)
            elif bit_metadata[:2] == '10':
                metadata['facing'] = 1
                metadata['head_offset'] = Vec3(-1, 0, 0)
            elif bit_metadata[:2] == '11':
                metadata['facing'] = 3
                metadata['head_offset'] = Vec3(1, 0, 0)
        elif bot.support_feature('blockMetadata'):
            bit_metadata = bin(bed_block.metadata)[2:].zfill(4)  # PART (1st bit), OCCUPIED (2nd bit), FACING (last 2 bits)
            metadata['part'] = bit_metadata[0] == '1'
            metadata['occupied'] = bit_metadata[1] == '1'

            if bit_metadata[2:4] == '01':
                metadata['facing'] = 1
                metadata['head_offset'] = Vec3(-1, 0, 0)
            elif bit_metadata[2:4] == '10':
                metadata['facing'] = 2
                metadata['head_offset'] = Vec3(0, 0, -1)
            elif bit_metadata[2:4] == '11':
                metadata['facing'] = 3
                metadata['head_offset'] = Vec3(1, 0, 0)

        return metadata

    async def wake():
        if not bot.is_sleeping:
            raise Exception('already awake')
        else:
            bot._client.write('entity_action', {
                'entityId': bot.entity.id,
                'actionId': 2,
                'jumpBoost': 0
            })

    async def sleep(bed_block):
        thunderstorm = bot.is_raining and (bot.thunder_state > 0)
        if not thunderstorm and not (12541 <= bot.time.time_of_day <= 23458):
            raise Exception("it's not night and it's not a thunderstorm")
        elif bot.is_sleeping:
            raise Exception('already sleeping')
        elif not is_a_bed(bed_block):
            raise Exception('wrong block: not a bed block')
        else:
            bot_pos = bot.entity.position.floored()
            metadata = parse_bed_metadata(bed_block)
            head_point = bed_block.position

            if metadata['occupied']:
                raise Exception('the bed is occupied')

            if not metadata['part']:  # Is foot
                upper_block = bot.block_at(bed_block.position + metadata['head_offset'])

                if is_a_bed(upper_block):
                    head_point = upper_block.position
                else:
                    lower_block = bot.block_at(bed_block.position + metadata['head_offset'].scaled(-1))

                    if is_a_bed(lower_block):
                        # If there are 2 foot parts, minecraft only lets you sleep if you click on the lower one
                        head_point = bed_block.position
                        bed_block = lower_block
                    else:
                        raise Exception("there's only half bed")

            if not bot.can_dig_block(bed_block):
                raise Exception('cant click the bed')

            click_range = [2, -3, -3, 2]  # [south, west, north, east]
            monster_range = [7, -8, -8, 7]
            opposite_cardinal = (metadata['facing'] + 2) % len(CARDINAL_DIRECTIONS)

            if click_range[opposite_cardinal] < 0:
                click_range[opposite_cardinal] -= 1
            else:
                click_range[opposite_cardinal] += 1

            nw_click_corner = head_point.offset(click_range[1], -2, click_range[2])  # North-West lower corner
            se_click_corner = head_point.offset(click_range[3], 2, click_range[0])  # South-East upper corner
            if not (nw_click_corner.x <= bot_pos.x <= se_click_corner.x
                    and nw_click_corner.y <= bot_pos.y <= se_click_corner.y
                    and nw_click_corner.z <= bot_pos.z <= se_click_corner.z):
                raise Exception('the bed is too far')

            if bot.game.game_mode != 'creative' or bot.support_feature('creativeSleepNearMobs'):
                # If in creative mode the bot should be able to sleep even if there are monsters nearby (starting in 1.13)
                nw_monster_corner = head_point.offset(monster_range[1], -6, monster_range[2])  # North-West lower corner
                se_monster_corner = head_point.offset(monster_range[3], 4, monster_range[0])  # South-East upper corner

                for entity_key in list(bot.entities.keys()):
                    entity = bot.entities[entity_key]
                    if entity.kind == 'Hostile mobs':
                        entity_pos = entity.position.floored()
                        if (nw_monster_corner.x <= entity_pos.x <= se_monster_corner.x
                                and nw_monster_corner.y <= entity_pos.y <= se_monster_corner.y
                                and nw_monster_corner.z <= entity_pos.z <= se_monster_corner.z):
                            raise Exception('there are monsters nearby')

            bot.activate_block(bed_block)

            await wait_until_sleep()

    async def wait_until_sleep():
        def sleep_handler(event_name, entity):
            if entity == bot.entity:
                bot.is_sleeping = True
                bot.emit('sleep')

        def wake_handler(event_name, entity):
            if entity == bot.entity:
                bot.is_sleeping = False
                bot.emit('wake')

        bot.once('entitySleep', sleep_handler)
        bot.once('entityWake', wake_handler)

        try:
            await bot.wait_for('sleep', timeout=3)
        except asyncio.TimeoutError:
            raise Exception('bot is not sleeping')

    bot._client.on('game_state_change', game_state_change_handler)
    bot.parse_bed_metadata = parse_bed_metadata
    bot.wake = wake
    bot.sleep = sleep
    bot.is_a_bed = is_a_bed
