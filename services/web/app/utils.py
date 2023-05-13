import numpy as np


def float_to_color(value: float) -> tuple:
    """
    Convert float to color in RGB format.
    Color is picked from red to green through yellow gradient.

    Args:
        value: Float in range [0, 1].
    """
    green = np.array([207, 246, 221])
    yellow = np.array([253, 245, 221])
    red = np.array([253, 221, 221])
    if value < 0.5:
        color = red + (yellow - red) * (value * 2)
    else:
        color = yellow + (green - yellow) * ((value - 0.5) * 2)
    return tuple(color.astype(int))
