import math

PI = math.pi
PI_2 = 2 * PI
TO_RAD = PI / 180
TO_DEG = 1 / TO_RAD
FROM_NOTCH_BYTE = 360 / 256
FROM_NOTCH_VEL = 1 / 8000

def to_radians(degrees):
    return TO_RAD * degrees

def to_degrees(radians):
    return TO_DEG * radians

def from_notchian_yaw(yaw):
    return euclidean_mod(PI - to_radians(yaw), PI_2)

def from_notchian_pitch(pitch):
    return euclidean_mod(to_radians(-pitch) + PI, PI_2) - PI

def from_notch_velocity(vel):
    return Vec3(vel.x * FROM_NOTCH_VEL, vel.y * FROM_NOTCH_VEL, vel.z * FROM_NOTCH_VEL)

def euclidean_mod(numerator, denominator):
    result = numerator % denominator
    return result + denominator if result < 0 else result

class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
