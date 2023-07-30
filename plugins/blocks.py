from vec3 import Vec3
import assert
from painting import Painting
from promise_utils import once_with_cleanup
from prismarine_world.iterators import OctahedronIterator

def inject(bot, version, storage_builder, hide_errors):
    Block = bot.registry.blocks.block
    Chunk = bot.registry.blocks.chunk
    World = bot.registry.blocks.world
    paintings_by_pos = {}
    paintings_by_id = {}

    def add_painting(painting):
        paintings_by_id[painting.id] = painting
        paintings_by_pos[painting.position] = painting

    def delete_painting(painting):
        del paintings_by_id[painting.id]
        del paintings_by_pos[painting.position]

    def del_column(chunk_x, chunk_z):
        bot.world.unload_column(chunk_x, chunk_z)

    def add_column(args):
        if not args["bitMap"] and args["groundUp"]:
            del_column(args["x"], args["z"])
            return
        column = bot.world.get_column(args["x"], args["z"])
        if not column:
            column = Chunk(min_y=bot.game.min_y, world_height=bot.game.height)
        try:
            column.load(args["data"], args["bitMap"], args["skyLightSent"], args["groundUp"])
            if "biomes" in args:
                column.load_biomes(args["biomes"])
            if "skyLight" in args:
                column.load_parsed_light(
                    args["skyLight"], args["blockLight"], args["skyLightMask"],
                    args["blockLightMask"], args["emptySkyLightMask"], args["emptyBlockLightMask"]
                )
            bot.world.set_column(args["x"], args["z"], column)
        except Exception as e:
            bot.emit("error", e)

    async def wait_for_chunks_to_load():
        dist = 2
        if not bot.entity.height:
            await once_with_cleanup(bot, "chunkColumnLoad")
        pos = bot.entity.position
        center = Vec3(pos.x >> 4 << 4, 0, pos.z >> 4 << 4)
        chunk_pos_to_check = set()
        for x in range(-dist, dist + 1):
            for z in range(-dist, dist + 1):
                pos = center + Vec3(x, 0, z) * 16
                if not bot.world.get_column_at(pos):
                    chunk_pos_to_check.add(str(pos))
        if chunk_pos_to_check:
            def wait_for_load_events(column_corner):
                chunk_pos_to_check.discard(str(column_corner))

            bot.world.on("chunkColumnLoad", wait_for_load_events)
            await once_with_cleanup(bot, lambda: not chunk_pos_to_check)
            bot.world.off("chunkColumnLoad", wait_for_load_events)

    def get_matching_function(matching):
        if callable(matching):
            return matching
        if not isinstance(matching, list):
            matching = [matching]

        def is_matching_type(block):
            return block is not None and block.type in matching

        return is_matching_type

    def is_block_in_section(section, matcher):
        if not section:
            return False
        if section.palette:
            for state_id in section.palette:
                if matcher(Block.from_state_id(state_id, 0)):
                    return True
            return False
        return True

    def get_full_matching_function(matcher, use_extra_info):
        if isinstance(use_extra_info, bool):
            if use_extra_info:
                return full_search_matcher_with_extra_info
            return non_full_search_matcher
        return non_full_search_matcher

    def non_full_search_matcher(point):
        block = block_at(point, True)
        return matcher(block)

    def full_search_matcher_with_extra_info(point):
        return matcher(block_at(point, use_extra_info=True))

    def find_blocks(options):
        matcher = get_matching_function(options["matching"])
        point = options.get("point", bot.entity.position).floored()
        max_distance = options.get("maxDistance", 16)
        count = options.get("count", 1)
        use_extra_info = options.get("useExtraInfo", False)
        full_matcher = get_full_matching_function(matcher, use_extra_info)
        start = Vec3(point.x // 16, point.y // 16, point.z // 16)
        it = OctahedronIterator(start, (max_distance + 8) // 16)
        visited_sections = set()
        blocks = []
        started_layer = 0
        next_ = start
        while next_:
            column = bot.world.get_column(next_.x, next_.z)
            section_y = next_.y + abs(bot.game.min_y) // 16
            total_sections = bot.game.height // 16
            if 0 <= section_y < total_sections and column and str(next_) not in visited_sections:
                section = column.sections[section_y]
                if use_extra_info or is_block_in_section(section, matcher):
                    begin = Vec3(next_.x * 16, section_y * 16 + bot.game.min_y, next_.z * 16)
                    cursor = begin.copy()
                    end = cursor + Vec3(16, 16, 16)
                    for cursor.x in range(begin.x, end.x):
                        for cursor.y in range(begin.y, end.y):
                            for cursor.z in range(begin.z, end.z):
                                if full_matcher(cursor) and cursor.distance_to(point) <= max_distance:
                                    blocks.append(cursor.copy())
                visited_sections.add(str(next_))
            if started_layer != it.apothem and len(blocks) >= count:
                break
            started_layer = it.apothem
            next_ = it.next()
        blocks.sort(key=lambda pos: pos.distance_to(point))
        if len(blocks) > count:
            blocks = blocks[:count]
        return blocks

    def find_block(options):
        blocks = find_blocks(options)
        if not blocks:
            return None
        return bot.block_at(blocks[0])

    def block_at(absolute_point, extra_infos=True):
        block = bot.world.get_block(absolute_point)
        if not block:
            return None
        if extra_infos:
            block.painting = paintings_by_pos.get(block.position)
        return block

    def can_see_block(block):
        head_pos = bot.entity.position + Vec3(0, bot.entity.height, 0)
        range_ = head_pos.distance_to(block.position)
        direction = block.position + Vec3(0.5, 0.5, 0.5) - head_pos
        def match(input_block, iter_):
            intersect = iter_.intersect(input_block.shapes, input_block.position)
            return intersect if intersect else input_block.position == block.position
        block_at_cursor = bot.world.raycast(head_pos, direction.normalize(), range_, match)
        return bool(block_at_cursor and block_at_cursor.position == block.position)

    def update_block_state(point, state_id):
        old_block = block_at(point)
        bot.world.set_block_state_id(point, state_id)
        new_block = block_at(point)
        if new_block is None:
            return
        if old_block.type != new_block.type:
            pos = point.floored()
            painting = paintings_by_pos.get(pos)
            if painting:
                delete_painting(painting)

    def update_sign(block, text, back=False):
        lines = text.split("\n")[:4]
        sign_data = {
            "text1": lines[0] if lines else "",
            "text2": lines[1] if len(lines) > 1 else "",
            "text3": lines[2] if len(lines) > 2 else "",
            "text4": lines[3] if len(lines) > 3 else ""
        }

        bot._client.write("update_sign", {
            "location": block.position,
            "isFrontText": not back,
            **sign_data
        })

    def dimension_to_folder_name(dimension):
        return dimensionNames.get(str(dimension), f"minecraft:dimension{dimension}")

    async def switch_world():
        if bot.world:
            if storage_builder:
                await bot.world.async.wait_saving()
            for name, listener in bot._events.items():
                if name.startswith("blockUpdate:"):
                    bot.emit(name, None, None)
                    bot.off(name, listener)
            for key in list(bot.world.async.columns.keys()):
                x, z = map(int, key.split(","))
                bot.world.unload_column(x, z)
            if storage_builder:
                bot.world.async.storage_provider = storage_builder({
                    "version": bot.version,
                    "worldName": dimension_to_folder_name(dimension)
                })
        else:
            bot.world = World(storage_builder({
                "version": bot.version,
                "worldName": dimension_to_folder_name(dimension)
            })) if storage_builder else World()
            start_listener_proxy()

    def start_listener_proxy():
        if listener:
            bot.off("newListener", listener)
            bot.off("removeListener", listener_remove)
        forwarded_events = ["blockUpdate", "chunkColumnLoad", "chunkColumnUnload"]
        for event in forwarded_events:
            bot.world.on(event, lambda *args: bot.emit(event, *args))
        block_update_regex = r"blockUpdate:\(-?\d+, -?\d+, -?\d+\)"
        def listener(event, listener):
            if block_update_regex.search(event):
                bot.world.on(event, listener)
        def listener_remove(event, listener):
            if block_update_regex.search(event):
                bot.world.off(event, listener)
        bot.on("newListener", listener)
        bot.on("removeListener", listener_remove)

    def ones_in_short(n):
        n = n & 0xFFFF
        count = 0
        for i in range(16):
            if (1 << i) & n:
                count += 1
        return count

    bot.find_blocks = find_blocks
    bot.find_block = find_block
    bot.can_see_block = can_see_block
    bot.block_at = block_at
    bot.update_block_state = update_block_state
    bot.update_sign = update_sign
    bot.wait_for_chunks_to_load = wait_for_chunks_to_load

    def on_login(packet):
        nonlocal dimension, worldName
        if bot.support_feature("dimensionIsAnInt"):
            dimension = packet.dimension
            worldName = dimension_to_folder_name(dimension)
        else:
            dimension = packet.dimension
            worldName = f"minecraft:{packet.worldName}"
        switch_world()

    def on_respawn(packet):
        in order to count the bits in the bit mask.

    bot._client.registerChannel("blockUpdate", [
        {
            "name": "location",
            "type": "u16",
            "parse": lambda value: {"x": value >> 12, "y": (value >> 8) & 0xF, "z": value & 0xFF}
        },
        {
            "name": "block",
            "type": "u16",
            "parse": lambda value: {
                "type": value >> 4,
                "metadata": value & 0xF,
                "paletteBit": ones_in_short(value) > 9
            }
        }
    ])
    bot._client.on("blockUpdate", lambda data: update_block_state(data["location"], data["block"]))

    bot.on("blockUpdate", lambda location, new_block: bot.emit(f"blockUpdate:{location}", location, new_block))

    bot.on("blockUpdate", lambda location, new_block: bot.emit(f"blockUpdate:{location['x'] & 31}, {location['z'] & 31}", location, new_block))

    bot.on("chunkColumnLoad", add_column)
    bot.on("chunkColumnUnload", del_column)

    async def shutdown():
        bot._client.unregisterChannel("blockUpdate")
        for name, listener in bot._events.items():
            if name.startswith("blockUpdate:"):
                bot.emit(name, None, None)
                bot.off(name, listener)
        for key in list(bot.world.async.columns.keys()):
            x, z = map(int, key.split(","))
            bot.world.unload_column(x, z)
        bot.world = None

    bot.once("end", shutdown)

    async def on_respawn(packet):
        if bot.support_feature("dimensionIsAnInt"):
            dimension = packet.dimension
        else:
            dimension = f"minecraft:{packet.worldName}"
        if dimension != worldName:
            await switch_world()

    bot._client.on("respawn", on_respawn)
    switch_world()
    return bot
