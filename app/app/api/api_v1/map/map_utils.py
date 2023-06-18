import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import settings
from app.models import Hexagon, Tile


def create_tile(hexagon_id, q_tile, r_tile):
    return Tile(q=q_tile, r=r_tile, hexagon_id=hexagon_id, type=0)


def get_tiles(hexagon_id, q, r):
    # For now, we will define each of the tiles in the hexagon separate
    return [
        create_tile(hexagon_id, q - 4, r + 0),
        create_tile(hexagon_id, q - 3, r - 1),
        create_tile(hexagon_id, q - 2, r - 2),
        create_tile(hexagon_id, q - 1, r - 3),
        create_tile(hexagon_id, q + 0, r - 4),
        create_tile(hexagon_id, q - 4, r + 1),
        create_tile(hexagon_id, q - 3, r + 0),
        create_tile(hexagon_id, q - 2, r - 1),
        create_tile(hexagon_id, q - 1, r - 2),
        create_tile(hexagon_id, q + 0, r - 3),
        create_tile(hexagon_id, q + 1, r - 4),
        create_tile(hexagon_id, q - 4, r + 2),
        create_tile(hexagon_id, q - 3, r + 1),
        create_tile(hexagon_id, q - 2, r + 0),
        create_tile(hexagon_id, q - 1, r - 1),
        create_tile(hexagon_id, q + 0, r - 2),
        create_tile(hexagon_id, q + 1, r - 3),
        create_tile(hexagon_id, q + 2, r - 4),
        create_tile(hexagon_id, q - 4, r + 3),
        create_tile(hexagon_id, q - 3, r + 2),
        create_tile(hexagon_id, q - 2, r + 1),
        create_tile(hexagon_id, q - 1, r + 0),
        create_tile(hexagon_id, q + 0, r - 1),
        create_tile(hexagon_id, q + 1, r - 2),
        create_tile(hexagon_id, q + 2, r - 3),
        create_tile(hexagon_id, q + 3, r - 4),
        create_tile(hexagon_id, q - 4, r + 4),
        create_tile(hexagon_id, q - 3, r + 3),
        create_tile(hexagon_id, q - 2, r + 2),
        create_tile(hexagon_id, q - 1, r + 1),
        create_tile(hexagon_id, q - 0, r + 0),
        create_tile(hexagon_id, q + 1, r - 1),
        create_tile(hexagon_id, q + 2, r - 2),
        create_tile(hexagon_id, q + 3, r - 3),
        create_tile(hexagon_id, q + 4, r - 4),
        create_tile(hexagon_id, q - 3, r + 4),
        create_tile(hexagon_id, q - 2, r + 3),
        create_tile(hexagon_id, q - 1, r + 2),
        create_tile(hexagon_id, q + 0, r + 1),
        create_tile(hexagon_id, q + 1, r + 0),
        create_tile(hexagon_id, q + 2, r - 1),
        create_tile(hexagon_id, q + 3, r - 2),
        create_tile(hexagon_id, q + 4, r - 3),
        create_tile(hexagon_id, q - 2, r + 4),
        create_tile(hexagon_id, q - 1, r + 3),
        create_tile(hexagon_id, q + 0, r + 2),
        create_tile(hexagon_id, q + 1, r + 1),
        create_tile(hexagon_id, q + 2, r + 0),
        create_tile(hexagon_id, q + 3, r - 1),
        create_tile(hexagon_id, q + 4, r - 2),
        create_tile(hexagon_id, q - 1, r + 4),
        create_tile(hexagon_id, q + 0, r + 3),
        create_tile(hexagon_id, q + 1, r + 2),
        create_tile(hexagon_id, q + 2, r + 1),
        create_tile(hexagon_id, q + 3, r + 0),
        create_tile(hexagon_id, q + 4, r - 1),
        create_tile(hexagon_id, q + 0, r + 4),
        create_tile(hexagon_id, q + 1, r + 3),
        create_tile(hexagon_id, q + 2, r + 2),
        create_tile(hexagon_id, q + 3, r + 1),
        create_tile(hexagon_id, q + 4, r + 0),
    ]


async def go_right(db: AsyncSession, q, r, q_tiles, r_tiles):
    # q = 9
    # r = -4
    # Go right so q += 1
    index = 0
    while index < settings.map_size:
        q += 1
        hexagon = Hexagon(q=q, r=r, tiles_detail="{}")
        db.add(hexagon)
        await db.commit()
        await db.refresh(hexagon)
        q_tiles += 9
        r_tiles -= 4
        tiles = get_tiles(hexagon.id, q_tiles, r_tiles)
        tiles_info = []
        for tile in tiles:
            db.add(tile)
            tiles_info.append(tile.serialize)
        hexagon.tiles_detail = json.dumps(tiles_info)
        db.add(hexagon)
        await db.commit()
        index += 1
    return [q, r, q_tiles, r_tiles]


async def go_left(db: AsyncSession, q, r, q_tiles, r_tiles):
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
        tiles = get_tiles(hexagon.id, q_tiles, r_tiles)
        tiles_info = []
        for tile in tiles:
            db.add(tile)
            tiles_info.append(tile.serialize)
        hexagon.tiles_detail = json.dumps(tiles_info)
        db.add(hexagon)
        await db.commit()
        index += 1
    return [q, r, q_tiles, r_tiles]


async def go_left_up(db: AsyncSession, q, r, q_tiles, r_tiles):
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
    tiles = get_tiles(hexagon.id, q_tiles, r_tiles)
    tiles_info = []
    for tile in tiles:
        db.add(tile)
        tiles_info.append(tile.serialize)
    hexagon.tiles_detail = json.dumps(tiles_info)
    db.add(hexagon)
    await db.commit()
    return [q, r, q_tiles, r_tiles]


async def go_right_down(db: AsyncSession, q, r, q_tiles, r_tiles):
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
    tiles = get_tiles(hexagon.id, q_tiles, r_tiles)
    tiles_info = []
    for tile in tiles:
        db.add(tile)
        tiles_info.append(tile.serialize)
    hexagon.tiles_detail = json.dumps(tiles_info)
    db.add(hexagon)
    await db.commit()
    return [q, r, q_tiles, r_tiles]
