class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

def loader(registry):
    class Particle:
        def __init__(self, id, position, offset, count=1, movementSpeed=0, longDistanceRender=False):
            self.id = id
            self.position = position
            self.offset = offset
            self.count = count
            self.movementSpeed = movementSpeed
            self.longDistanceRender = longDistanceRender

        @classmethod
        def from_network(cls, packet):
            return cls(
                packet['particleId'],
                Vec3(packet['x'], packet['y'], packet['z']),
                Vec3(packet['offsetX'], packet['offsetY'], packet['offsetZ']),
                packet['particles'],
                packet['particleData'],
                packet['longDistance']
            )

    return Particle
