from app.config import DevelopmentConfig


def get_wraparounds(q, r):
    map_size = DevelopmentConfig.map_size
    wrap_q = 0
    wrap_r = 0
    if q < -map_size:
        while q < -map_size:
            q = q + (2 * map_size + 1)
            wrap_q -= 1
    if q > map_size:
        while q > map_size:
            q = q - (2 * map_size + 1)
            wrap_q += 1
    if r < -map_size:
        while r < -map_size:
            r = r + (2 * map_size + 1)
            wrap_r -= 1
    if r > map_size:
        while r > map_size:
            r = r - (2 * map_size + 1)
            wrap_r += 1
    return [q, wrap_q, r, wrap_r]
