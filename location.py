class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def floored(self):
        return Vec3(int(self.x), int(self.y), int(self.z))

    def modulus(self, other):
        return Vec3(self.x % other.x, self.y % other.y, self.z % other.z)

    def minus(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

CHUNK_SIZE = Vec3(16, 16, 16)

class Location:
    def __init__(self, absolute_vector):
        self.floored = absolute_vector.floored()
        self.block_point = self.floored.modulus(CHUNK_SIZE)
        self.chunk_corner = self.floored.minus(self.block_point)
        self.block_index = self.block_point.x + CHUNK_SIZE.x * self.block_point.z + CHUNK_SIZE.x * CHUNK_SIZE.z * self.block_point.y
        self.biome_block_index = self.block_point.x + CHUNK_SIZE.x * self.block_point.z
        self.chunk_y_index = int(absolute_vector.y / 16)

