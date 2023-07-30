import asyncio
from typing import Optional
from math import sqrt

class Vec3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def minus(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scaled(self, factor: float):
        return Vec3(self.x * factor, self.y * factor, self.z * factor)


async def fly_to(bot, destination: Vec3):
    normal_gravity = None
    flying_speed_per_update = 0.5

    def vec_magnitude(vec):
        return sqrt(vec.x * vec.x + vec.y * vec.y + vec.z * vec.z)

    def start_flying():
        nonlocal normal_gravity
        if normal_gravity is None:
            normal_gravity = bot.physics.gravity
        bot.physics.gravity = 0

    def stop_flying():
        nonlocal normal_gravity
        bot.physics.gravity = normal_gravity

    # straight line, so make sure there's a clear path.
    start_flying()

    vector = destination.minus(bot.entity.position)
    magnitude = vec_magnitude(vector)

    while magnitude > flying_speed_per_update:
        bot.physics.gravity = 0
        bot.entity.velocity = Vec3(0, 0, 0)

        # small steps
        normalized_vector = vector.scaled(1 / magnitude)
        bot.entity.position = bot.entity.position.plus(normalized_vector.scaled(flying_speed_per_update))

        await asyncio.sleep(0.05)

        vector = destination.minus(bot.entity.position)
        magnitude = vec_magnitude(vector)

    # last step
    bot.entity.position = destination
    await bot.once('move')

    stop_flying()
