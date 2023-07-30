import asyncio
import time
from typing import Union

class Vec3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def offset(self, x: float, y: float, z: float):
        return Vec3(self.x + x, self.y + y, self.z + z)

    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return (dx * dx + dy * dy + dz * dz) ** 0.5

class Block:
    def __init__(self, position: Vec3, diggable: bool):
        self.position = position
        self.diggable = diggable

def inject(bot):

    swing_interval = None
    wait_timeout = None

    digging_task = None
    bot.target_dig_block = None
    bot.last_dig_time = None

    async def dig(block: Block, force_look=False, dig_face: Union[str, Vec3] = 'auto'):
        nonlocal digging_task

        if block is None:
            raise ValueError('dig was called with an undefined or null block')

        if dig_face is None or isinstance(dig_face, Vec3):
            dig_face = 'auto'

        if bot.target_dig_block:
            bot.stop_digging()

        digging_face = 1  # Default (top)

        if force_look != 'ignore':
            if isinstance(dig_face, Vec3):
                if dig_face.x:
                    digging_face = BlockFaces.EAST if dig_face.x > 0 else BlockFaces.WEST
                elif dig_face.y:
                    digging_face = BlockFaces.TOP if dig_face.y > 0 else BlockFaces.BOTTOM
                elif dig_face.z:
                    digging_face = BlockFaces.SOUTH if dig_face.z > 0 else BlockFaces.NORTH
                await bot.look_at(
                    block.position.offset(0.5, 0.5, 0.5).offset(dig_face.x * 0.5, dig_face.y * 0.5, dig_face.z * 0.5),
                    force_look
                )
            elif dig_face == 'raycast':
                dx = bot.entity.position.x - (block.position.x + 0.5)
                dy = bot.entity.position.y + bot.entity.height - (block.position.y + 0.5)
                dz = bot.entity.position.z - (block.position.z + 0.5)

                visible_faces = {
                    'y': int(abs(dy) > 0.5),
                    'x': int(abs(dx) > 0.5),
                    'z': int(abs(dz) > 0.5)
                }

                valid_faces = []
                for face, visible in visible_faces.items():
                    if not visible:
                        continue

                    target_pos = block.position.offset(
                        0.5 + (visible_faces['x'] * 0.5 if face == 'x' else 0),
                        0.5 + (visible_faces['y'] * 0.5 if face == 'y' else 0),
                        0.5 + (visible_faces['z'] * 0.5 if face == 'z' else 0)
                    )

                    start_pos = bot.entity.position.offset(0, bot.entity.height, 0)
                    ray_block = bot.world.raycast(start_pos, target_pos.minus(start_pos).normalize(), 5)
                    if ray_block:
                        ray_pos = ray_block.position
                        if ray_pos.x == block.position.x and ray_pos.y == block.position.y and ray_pos.z == block.position.z:
                            valid_faces.append({
                                'face': ray_block.face,
                                'target_pos': ray_block.intersect
                            })

                if valid_faces:
                    closest = None
                    dist_sqrt = 999
                    for valid_face in valid_faces:
                        t_pos = valid_face['target_pos']
                        c_dist = Vec3(t_pos.x, t_pos.y, t_pos.z).distance_to(
                            bot.entity.position.offset(0, bot.entity.height, 0)
                        )
                        if dist_sqrt > c_dist:
                            closest = valid_face
                            dist_sqrt = c_dist

                    await bot.look_at(closest['target_pos'], force_look)
                    digging_face = closest['face']
                else:
                    raise ValueError('Block not in view')
            else:
                await bot.look_at(block.position.offset(0.5, 0.5, 0.5), force_look)

        digging_task = asyncio.create_task(do_digging(block, digging_face))
        await digging_task

    async def do_digging(block: Block, digging_face: int):
        nonlocal swing_interval, wait_timeout, digging_task

        if swing_interval or wait_timeout:
            raise RuntimeError('Digging is already in progress')

        def finish_digging():
            nonlocal swing_interval, wait_timeout
            swing_interval = None
            wait_timeout = None

            if bot.target_dig_block:
                bot._client.write('block_dig', {
                    'status': 2,  # finish digging
                    'location': bot.target_dig_block.position,
                    'face': digging_face  # hard coded to always dig from the top
                })

            bot.target_dig_block = None
            bot.last_dig_time = time.perf_counter()

        def on_block_update(old_block, new_block):
            nonlocal swing_interval, wait_timeout, digging_task
            if new_block is None or new_block.type != 0:
                return

            bot.remove_listener('blockUpdate', on_block_update)
            if swing_interval:
                swing_interval.cancel()
                swing_interval = None

            if wait_timeout:
                wait_timeout.cancel()
                wait_timeout = None

            bot.target_dig_block = None
            bot.last_dig_time = time.perf_counter()

            digging_task.set_result(None)

        bot.target_dig_block = block
        bot._client.write('block_dig', {
            'status': 0,  # start digging
            'location': block.position,
            'face': digging_face  # default face is 1 (top)
        })

        wait_time = dig_time(block)
        wait_timeout = asyncio.create_task(asyncio.sleep(wait_time))
        swing_interval = asyncio.create_task(do_swing_interval())

        bot.swing_arm()

        def do_swing_arm():
            bot.swing_arm()

        async def do_swing_interval():
            while True:
                do_swing_arm()
                await asyncio.sleep(0.35)

        bot.add_listener('blockUpdate', on_block_update)

    def stop_digging():
        nonlocal swing_interval, wait_timeout, digging_task

        if swing_interval:
            swing_interval.cancel()
            swing_interval = None

        if wait_timeout:
            wait_timeout.cancel()
            wait_timeout = None

        if bot.target_dig_block:
            bot._client.write('block_dig', {
                'status': 1,  # cancel digging
                'location': bot.target_dig_block.position,
                'face': 1  # hard coded to always dig from the top
            })

            block = bot.target_dig_block
            bot.target_dig_block = None
            bot.last_dig_time = time.perf_counter()

            bot.remove_listener('blockUpdate', on_block_update)
            bot.emit('diggingAborted', block)

            digging_task.cancel()

    def can_dig_block(block: Block):
        if not block or not block.diggable:
            return False

        return block.position.offset(0.5, 0.5, 0.5).distance_to(
            bot.entity.position.offset(0, 1.65, 0)
        ) <= 5.1

    def dig_time(block: Block):
        type_id = None
        enchantments = []

        currently_held_item = bot.held_item
        if currently_held_item:
            type_id = currently_held_item.type
            enchantments = currently_held_item.enchants

        head_equipment_slot = bot.get_equipment_dest_slot('head')
        head_equipped_item = bot.inventory.slots[head_equipment_slot]
        if head_equipped_item:
            helmet_enchantments = head_equipped_item.enchants
            enchantments.extend(helmet_enchantments)

        creative = bot.game.game_mode == 'creative'
        return block.dig_time(
            type_id,
            creative,
            bot.entity.is_in_water,
            not bot.entity.on_ground,
            enchantments,
            bot.entity.effects
        )

    async def look_at(position: Vec3, force_look):
        # Implement look_at logic
        pass

    # Constants from BlockFaces class
    class BlockFaces:
        EAST = 5
        WEST = 4
        TOP = 1
        BOTTOM = 0
        SOUTH = 3
        NORTH = 2

    bot.dig = dig
    bot.stop_digging = stop_digging
    bot.can_dig_block = can_dig_block
    bot.dig_time = dig_time

    bot.target_dig_block = None
    bot.last_dig_time = None
    bot.add_listener('death', lambda: stop_digging())
