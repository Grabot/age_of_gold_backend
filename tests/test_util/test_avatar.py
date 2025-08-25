# ruff: noqa: E402
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

import filecmp
import math
import os

import pytest

from app.util.avatar import (
    Line,
    Plane,
    Point,
    add_square_clean,
    angle_slopes,
    background_square_clean,
    check_lengths,
    generate_avatar,
    get_angle_lines,
    get_length,
    point_on_line,
    point_on_plane_border,
    slope_line,
)


def test_generate_avatar() -> None:
    test_path = os.path.join(current_dir.parent, "data")

    generate_avatar(file_name="test", file_path=str(test_path))

    generated_avatar_path = os.path.join(test_path, "test_default.png")
    default_avatar_path = os.path.join(test_path, "test_default_copy.png")

    assert filecmp.cmp(
        str(generated_avatar_path), str(default_avatar_path), shallow=False
    ), "The generated avatar does not match the default avatar"

    os.remove(str(generated_avatar_path))


def test_line_class() -> None:
    line = Line((0, 0), (3, 4))
    assert line.start == (0, 0)
    assert line.end == (3, 4)
    assert line.get_length() == 5.0

    line_same_point = Line((0, 0), (0, 0))
    assert line_same_point.start == (0, 0)
    assert line_same_point.end == (0, 0)
    assert line_same_point.get_length() == 0.0

    line_negative = Line((-1, -1), (-4, -5))
    assert line_negative.start == (-1, -1)
    assert line_negative.end == (-4, -5)
    assert line_negative.get_length() == 5.0

    line_one_negative = Line((1, -1), (4, -5))
    assert line_one_negative.start == (1, -1)
    assert line_one_negative.end == (4, -5)
    assert line_one_negative.get_length() == 5.0

    line_next = Line((0, 0), (3, 4))
    line_next.set_next(line)
    assert line_next.get_next() == line


def test_plane_class() -> None:
    points: list[Point] = [(0, 0), (3, 0), (3, 3), (0, 3)]
    plane = Plane(points, "#FF0000")
    assert plane.points == points
    assert plane.get_colour() == "#FF0000"
    assert len(plane.get_all_lines()) == 4

    line1 = plane.get_line(0)
    line2 = plane.get_line(1)
    line3 = plane.get_line(2)
    line4 = plane.get_line(3)

    assert line1.get_next() == line2
    assert line2.get_next() == line3
    assert line3.get_next() == line4
    assert line4.get_next() == line1


def test_get_angle_lines() -> None:
    line1 = Line((0, 0), (1, 0))
    line2 = Line((1, 0), (1, 1))
    angle_line: float = get_angle_lines(line1, line2)
    assert angle_line >= 89.9
    assert angle_line <= 90.1

    line3 = Line((0, 0), (1, 0))
    line4 = Line((1, 0), (2, 0))
    angle_line_same_slope: float = get_angle_lines(line3, line4)
    assert angle_line_same_slope == 0.0

    line5 = Line((0, 0), (1, 0))
    line6 = Line((1, 0), (1, 1))
    angle_line_perpendicular: float = get_angle_lines(line5, line6)
    assert angle_line_perpendicular >= 89.9
    assert angle_line_perpendicular <= 90.1

    line7 = Line((0, 0), (1, -1))
    line8 = Line((1, -1), (2, -2))
    angle_line_negative_slope: float = get_angle_lines(line7, line8)
    assert angle_line_negative_slope == 0.0

    line9 = Line((0, 0), (1, 1))
    line10 = Line((1, 1), (2, 0))
    angle_line_one_negative_slope: float = get_angle_lines(line9, line10)
    assert angle_line_one_negative_slope >= 89.9
    assert angle_line_one_negative_slope <= 90.1


def test_slope_line() -> None:
    assert slope_line((0, 0), (1, 1)) == 1.0
    assert slope_line((0, 0), (1, 0)) == 0.0
    assert slope_line((0, 0), (1, math.sqrt(3))) == math.sqrt(3)
    assert slope_line((0, 0), (1, -1)) == -1.0
    assert slope_line((0, 0), (1, 0)) == 0.0
    assert slope_line((0, 0), (1, math.sqrt(3) / 3)) == math.sqrt(3) / 3
    assert slope_line((0, 0), (1, -math.sqrt(3) / 3)) == -math.sqrt(3) / 3


def test_angle_slopes() -> None:
    angle_45: float = angle_slopes(1.0, 0.0)
    # Angle should be 45 or -45, which will be turned to positive 135
    assert angle_45 == 45.0 or angle_45 == 135

    angle_15 = angle_slopes(1.0, math.sqrt(3))
    assert angle_15 >= 14.9 and angle_15 <= 15.1

    angle_30 = angle_slopes(0.0, math.sqrt(3) / 3)
    assert angle_30 >= 29.9 and angle_30 <= 30.1


def test_point_on_line() -> None:
    line = Line((0, 0), (3, 3))
    assert point_on_line(line, (1, 1))


def test_point_on_plane_border() -> None:
    points: list[Point] = [(0, 0), (3, 0), (3, 3), (0, 3)]
    plane = Plane(points, "#FF0000")
    assert point_on_plane_border(plane, (1, 0))
    assert not point_on_plane_border(plane, (1, 1))


def test_get_length() -> None:
    assert get_length((0, 0), (0, 0)) == 0.0
    assert get_length((0, 0), (1, 0)) == 1.0
    assert get_length((0, 0), (1, 1)) == math.sqrt(2)
    assert get_length((0, 0), (3, 4)) == 5.0


def test_check_lengths() -> None:
    points: list[Point] = [(0, 0), (3, 0), (3, 3), (0, 3)]
    assert check_lengths(points, 2)


def test_add_square_clean() -> None:
    width = 252
    height = 252
    planes = [background_square_clean(width, height, 0)]
    plane1, plane2, chosen_plane = add_square_clean(width, height, planes, 0)
    assert plane1 is not None
    assert plane2 is not None
    assert chosen_plane is not None


def test_background_square_clean() -> None:
    width = 252
    height = 252
    plane = background_square_clean(width, height, 0)
    assert plane is not None
    assert len(plane.get_all_lines()) == 4


if __name__ == "__main__":
    pytest.main([__file__])
