from functools import wraps
from urllib.error import HTTPError
from requests.exceptions import ConnectionError

from flask import session, redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user

from common.constants import UserRole


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
            res = {}
            try:
                res = func(*args, **kwargs)
                res = res if isinstance(res, dict) else {}
            except HTTPError as e:
                flash(f'HTTPError: {e.status} {e.msg}', 'error')
            except ConnectionError as e:
                flash(f'ConnectionError: {e}', 'error')
            res.update(request.args)
            if endpoint in session:
                res.update(session[endpoint])
            return redirect(url_for(endpoint, **res))
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
                error = f'HTTPError: {e.status} {e.msg}'
                return render_template('error.html', error=error)
            except ConnectionError as e:
                error = f'ConnectionError: {e}'
                return render_template('error.html', error=error)
        return wrapper
    return decorator


def role_required(role: UserRole):
    """
    Decorator for checking user role.
    Redirects to index if user role is not specified.

    Args:
        role: Required user role.
    """
    def decorator(func: callable):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in (role, UserRole.ADMIN):
                flash('You do not have access to this page', 'error')
                return redirect(url_for('main.index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator
