from flask import request, session

from app.blueprints.users import bp
from app.utils import render, action, role_required
from app import api_client
from app.schemas import UserCreate, UserRole


@bp.before_request
@role_required(UserRole.ADMIN)
def before_request():
    pass


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
        role=UserRole.USER
    )
    api_client.users.create(user_schema)


@bp.route('/delete/<int:id>', methods=['POST'])
@action(endpoint='users.manage')
def delete(id: int):
    api_client.users.delete(id)
