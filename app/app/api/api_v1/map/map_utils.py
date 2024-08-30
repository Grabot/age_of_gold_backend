import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import settings
from app.models import Hexagon, Tile
import numpy as np


def create_tile(hexagon_id, q_tile, r_tile, noise):
    if noise[q_tile][r_tile] < 0:
        return Tile(q=q_tile, r=r_tile, hexagon_id=hexagon_id, type=2)
    else:
        return Tile(q=q_tile, r=r_tile, hexagon_id=hexagon_id, type=9)


def get_tiles(hexagon_id, q, r, noise):
    # For now, we will define each of the tiles in the hexagon separate
    return [
        create_tile(hexagon_id, q - 4, r + 0, noise),
        create_tile(hexagon_id, q - 3, r - 1, noise),
        create_tile(hexagon_id, q - 2, r - 2, noise),
        create_tile(hexagon_id, q - 1, r - 3, noise),
        create_tile(hexagon_id, q + 0, r - 4, noise),
        create_tile(hexagon_id, q - 4, r + 1, noise),
        create_tile(hexagon_id, q - 3, r + 0, noise),
        create_tile(hexagon_id, q - 2, r - 1, noise),
        create_tile(hexagon_id, q - 1, r - 2, noise),
        create_tile(hexagon_id, q + 0, r - 3, noise),
        create_tile(hexagon_id, q + 1, r - 4, noise),
        create_tile(hexagon_id, q - 4, r + 2, noise),
        create_tile(hexagon_id, q - 3, r + 1, noise),
        create_tile(hexagon_id, q - 2, r + 0, noise),
        create_tile(hexagon_id, q - 1, r - 1, noise),
        create_tile(hexagon_id, q + 0, r - 2, noise),
        create_tile(hexagon_id, q + 1, r - 3, noise),
        create_tile(hexagon_id, q + 2, r - 4, noise),
        create_tile(hexagon_id, q - 4, r + 3, noise),
        create_tile(hexagon_id, q - 3, r + 2, noise),
        create_tile(hexagon_id, q - 2, r + 1, noise),
        create_tile(hexagon_id, q - 1, r + 0, noise),
        create_tile(hexagon_id, q + 0, r - 1, noise),
        create_tile(hexagon_id, q + 1, r - 2, noise),
        create_tile(hexagon_id, q + 2, r - 3, noise),
        create_tile(hexagon_id, q + 3, r - 4, noise),
        create_tile(hexagon_id, q - 4, r + 4, noise),
        create_tile(hexagon_id, q - 3, r + 3, noise),
        create_tile(hexagon_id, q - 2, r + 2, noise),
        create_tile(hexagon_id, q - 1, r + 1, noise),
        create_tile(hexagon_id, q - 0, r + 0, noise),
        create_tile(hexagon_id, q + 1, r - 1, noise),
        create_tile(hexagon_id, q + 2, r - 2, noise),
        create_tile(hexagon_id, q + 3, r - 3, noise),
        create_tile(hexagon_id, q + 4, r - 4, noise),
        create_tile(hexagon_id, q - 3, r + 4, noise),
        create_tile(hexagon_id, q - 2, r + 3, noise),
        create_tile(hexagon_id, q - 1, r + 2, noise),
        create_tile(hexagon_id, q + 0, r + 1, noise),
        create_tile(hexagon_id, q + 1, r + 0, noise),
        create_tile(hexagon_id, q + 2, r - 1, noise),
        create_tile(hexagon_id, q + 3, r - 2, noise),
        create_tile(hexagon_id, q + 4, r - 3, noise),
        create_tile(hexagon_id, q - 2, r + 4, noise),
        create_tile(hexagon_id, q - 1, r + 3, noise),
        create_tile(hexagon_id, q + 0, r + 2, noise),
        create_tile(hexagon_id, q + 1, r + 1, noise),
        create_tile(hexagon_id, q + 2, r + 0, noise),
        create_tile(hexagon_id, q + 3, r - 1, noise),
        create_tile(hexagon_id, q + 4, r - 2, noise),
        create_tile(hexagon_id, q - 1, r + 4, noise),
        create_tile(hexagon_id, q + 0, r + 3, noise),
        create_tile(hexagon_id, q + 1, r + 2, noise),
        create_tile(hexagon_id, q + 2, r + 1, noise),
        create_tile(hexagon_id, q + 3, r + 0, noise),
        create_tile(hexagon_id, q + 4, r - 1, noise),
        create_tile(hexagon_id, q + 0, r + 4, noise),
        create_tile(hexagon_id, q + 1, r + 3, noise),
        create_tile(hexagon_id, q + 2, r + 2, noise),
        create_tile(hexagon_id, q + 3, r + 1, noise),
        create_tile(hexagon_id, q + 4, r + 0, noise),
    ]


async def go_right(db: AsyncSession, q, r, q_tiles, r_tiles, distance, noise):
    # q = 9
    # r = -4
    # Go right so q += 1
    index = 0
    while index < distance:
        q += 1
        hexagon = Hexagon(q=q, r=r, tiles_detail="{}")
        db.add(hexagon)
        await db.commit()
        await db.refresh(hexagon)
        q_tiles += 9
        r_tiles -= 4
        tiles = get_tiles(hexagon.id, q_tiles, r_tiles, noise)
        tiles_info = []
        for tile in tiles:
            db.add(tile)
            tiles_info.append(tile.serialize)
        hexagon.tiles_detail = json.dumps(tiles_info)
        db.add(hexagon)
        await db.commit()
        index += 1
    return [q, r, q_tiles, r_tiles]


async def go_left(db: AsyncSession, q, r, q_tiles, r_tiles, noise):
    # q = -9
    # r = 4
    # Go left so q -= 1
    index = 0
    while index < settings.map_size:
        q -= 1
        hexagon = Hexagon(q=q, r=r, tiles_detail="{}")
        db.add(hexagon)
        await db.commit()
        await db.refresh(hexagon)
        q_tiles -= 9
        r_tiles += 4
        tiles = get_tiles(hexagon.id, q_tiles, r_tiles, noise)
        tiles_info = []
        for tile in tiles:
            db.add(tile)
            tiles_info.append(tile.serialize)
        hexagon.tiles_detail = json.dumps(tiles_info)
        db.add(hexagon)
        await db.commit()
        index += 1
    return [q, r, q_tiles, r_tiles]


async def go_left_up(db: AsyncSession, q, r, q_tiles, r_tiles, noise):
    # q = -5
    # r = 9
    # go left up, so q += 0 r -= 1
    r -= 1
    hexagon = Hexagon(q=q, r=r, tiles_detail="{}")
    db.add(hexagon)
    await db.commit()
    await db.refresh(hexagon)
    q_tiles -= 5
    r_tiles += 9
    tiles = get_tiles(hexagon.id, q_tiles, r_tiles, noise)
    tiles_info = []
    for tile in tiles:
        db.add(tile)
        tiles_info.append(tile.serialize)
    hexagon.tiles_detail = json.dumps(tiles_info)
    db.add(hexagon)
    await db.commit()
    return [q, r, q_tiles, r_tiles]


async def go_right_down(db: AsyncSession, q, r, q_tiles, r_tiles, noise):
    # q = 5
    # r = -9
    # Go right down so r += 1 and s -= 1
    r += 1
    hexagon = Hexagon(q=q, r=r, tiles_detail="{}")
    db.add(hexagon)
    await db.commit()
    await db.refresh(hexagon)
    q_tiles += 5
    r_tiles -= 9
    tiles = get_tiles(hexagon.id, q_tiles, r_tiles, noise)
    tiles_info = []
    for tile in tiles:
        db.add(tile)
        tiles_info.append(tile.serialize)
    hexagon.tiles_detail = json.dumps(tiles_info)
    db.add(hexagon)
    await db.commit()
    return [q, r, q_tiles, r_tiles]


def generate_perlin_noise_2d(shape, res):
    def f(t):
        return 6*t**5 - 15*t**4 + 10*t**3

    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0],0:res[1]:delta[1]].transpose(1, 2, 0) % 1
    # Gradients
    angles = 2*np.pi*np.random.rand(res[0]+1, res[1]+1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1,0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:,0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1,1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:,1:].repeat(d[0], 0).repeat(d[1], 1)
    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:,:,0]-1, grid[:,:,1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:,:,0], grid[:,:,1]-1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:,:,0]-1, grid[:,:,1]-1)) * g11, 2)
    # Interpolation
    t = f(grid)
    n0 = n00*(1-t[:,:,0]) + t[:,:,0]*n10
    n1 = n01*(1-t[:,:,0]) + t[:,:,0]*n11
    return np.sqrt(2)*((1-t[:,:,1])*n0 + t[:,:,1]*n1)


def generate_fractal_noise_2d(shape, res, octaves=1, persistence=0.5):
    noise = np.zeros(shape)
    frequency = 1
    amplitude = 1
    for _ in range(octaves):
        noise += amplitude * generate_perlin_noise_2d(shape, (frequency*res[0], frequency*res[1]))
        frequency *= 2
        amplitude *= persistence
    return noise

