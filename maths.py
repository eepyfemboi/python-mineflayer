def clamp(min_val, x, max_val):
    return max(min_val, min(x, max_val))

def euclidean_mod(numerator, denominator):
    result = numerator % denominator
    return result + denominator if result < 0 else result
