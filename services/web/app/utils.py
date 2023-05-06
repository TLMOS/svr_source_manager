from functools import wraps
from urllib.error import HTTPError
from requests.exceptions import ConnectionError
import numpy as np

from flask import session, redirect, url_for, render_template, request


def action(endpoint: str):
    """
    Decorator for url actions (redirects).
    On HTTPError, redirects to endpoint with error message.
    Pulls data from session if endpoint is specified.

    Args:
        endpoint: Endpoint to redirect to.
    """
    def decorator(func: callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error, res = None, {}
            try:
                res = func(*args, **kwargs)
                res = res if isinstance(res, dict) else {}
            except HTTPError as e:
                if e.code == 401:
                    return ('Unauthorized', 401, {
                                'WWW-Authenticate': 'Basic realm="Login Required"'
                            })
                error = f'HTTPError: {e.status} {e.msg}'
            except ConnectionError as e:
                error = f'ConnectionError: {e}'
            res.update(request.args)
            if endpoint in session:
                res.update(session[endpoint])
            return redirect(url_for(endpoint, error=error, **res))
        return wrapper
    return decorator


def render(template: str, endpoint: str = None):
    """
    Decorator for rendering templates.
    On HTTPError, renders error.html template.
    Pulls data from session if endpoint is specified.

    Args:
        template: Template to render.
        endpoint: Endpoint to pull data from session.
    """
    def decorator(func: callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                res = res if isinstance(res, dict) else {}
                if endpoint and endpoint in session:
                    res.update(session[endpoint])
                res.update(request.args)
                return render_template(template, **res)
            except HTTPError as e:
                if e.code == 401:
                    return ('Unauthorized', 401, {
                                'WWW-Authenticate': 'Basic realm="Login Required"'
                            })
                error = f'HTTPError: {e.status} {e.msg}'
                return render_template('error.html', error=error)
            except ConnectionError as e:
                error = f'ConnectionError: {e}'
                return render_template('error.html', error=error)
        return wrapper
    return decorator


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
