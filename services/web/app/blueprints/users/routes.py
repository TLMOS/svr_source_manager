from urllib.error import HTTPError

from flask import request, session

from app.blueprints.users import bp
from app.utils import render, action
from app import api_client
from app.schemas import UserCreate


@bp.route('/manage', methods=['GET'])
@render(template='users/manage.html', endpoint='users.manage')
def manage():
    search_entry = request.args.get('search_entry', '')

    users = api_client.users.get_all()
    if search_entry:
        users = [u for u in users if search_entry in u.name]
    sources = api_client.sources.get_all()
    source_count = {}
    for source in sources:
        if source.user_id not in source_count:
            source_count[source.user_id] = 0
        source_count[source.user_id] += 1
    for user in users:
        if user.id in source_count:
            count = source_count[user.id]
        else:
            count = 0
        source_count[user.id] = '{current}/{max}'.format_map({
            'current': count,
            'max': user.max_sources if user.max_sources >= 0 else '∞'
        })
    session['users.manage'] = {
        'search_entry': search_entry,
    }
    return {
        'users': users,
        'source_count': source_count
    }


@bp.route('/forget', methods=['GET'])
@action(endpoint='main.index')
def forget():
    api_client.users.forget()


@bp.route('/me', methods=['GET'])
@render(template='users/user.html', endpoint='users.me')
def me():
    user = api_client.users.me()
    return {
        'user': user
    }


@bp.route('/update/password/<int:id>', methods=['POST'])
@action(endpoint='users.me')
def update_password(id: int):
    password = request.form['password']
    if not password:
        raise HTTPError(None, 400, 'Password cannot be empty', None, None)
    api_client.users.update_password(id, password)


@bp.route('/add', methods=['POST'])
@action(endpoint='users.manage')
def add():
    name = request.form['name']
    password = request.form['password']
    max_sources = int(request.form['max_sources'])
    user_schema = UserCreate(
        name=name,
        password=password,
        max_sources=max_sources,
        is_admin=False
    )
    api_client.users.create(user_schema)


@bp.route('/delete/<int:id>', methods=['POST'])
@action(endpoint='users.manage')
def delete(id: int):
    api_client.users.delete(id)
