"""Geographic utilities: Douglas-Peucker simplification."""
import math


def _perpendicular_distance(point: tuple, line_start: tuple, line_end: tuple) -> float:
    """Perpendicular distance from point to a line segment (in coordinate space)."""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x0 - x1, y0 - y1)
    t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    return math.hypot(x0 - (x1 + t * dx), y0 - (y1 + t * dy))


def douglas_peucker(points: list[tuple[float, float]], epsilon: float) -> list[tuple[float, float]]:
    """
    Simplify a polyline using the Ramer-Douglas-Peucker algorithm.
    points: list of (lat, lng) tuples
    epsilon: maximum distance threshold in degrees
    Returns simplified list of (lat, lng) tuples.
    """
    if len(points) <= 2:
        return points

    max_dist = 0.0
    max_idx = 0
    start, end = points[0], points[-1]

    for i in range(1, len(points) - 1):
        dist = _perpendicular_distance(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > epsilon:
        left = douglas_peucker(points[:max_idx + 1], epsilon)
        right = douglas_peucker(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]


def simplify_route(
    points: list[tuple[float, float]],
    target_points: int = 200,
) -> list[tuple[float, float]]:
    """
    Simplify a route to approximately target_points using Douglas-Peucker.
    Automatically adjusts epsilon to hit the target count.
    """
    if len(points) <= target_points:
        return points

    # Binary search for epsilon that yields approximately target_points
    lo, hi = 0.0, 1.0
    result = points
    for _ in range(20):
        mid = (lo + hi) / 2
        simplified = douglas_peucker(points, mid)
        if len(simplified) > target_points:
            lo = mid
        else:
            result = simplified
            hi = mid
        if abs(len(result) - target_points) <= max(1, target_points * 0.1):
            break

    return result
