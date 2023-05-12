from datetime import datetime
from datetime import timedelta
from urllib.error import HTTPError
import base64

from flask import request, session
from flask_login import login_required

from app.blueprints.sources import bp
from app import api_client
from app.schemas import SourceStatus
from app.utils import float_to_color, action, render


@bp.before_request
@login_required
def before_request():
    pass


@bp.route('/', methods=['GET', 'POST'])
@render(template='sources/index.html', endpoint='sources.index')
def index():
    search_entry = request.args.get('search_entry', '')
    show_finished = request.args.get('show_finished', 'off')

    sources = api_client.sources.get_all()
    if show_finished == 'off':
        sources = [
            s for s in sources if s.status_code != SourceStatus.FINISHED
        ]
    if search_entry:
        sources = [s for s in sources if search_entry in s.name]
    sources.sort(key=lambda s: s.name)
    sources.sort(key=lambda s: s.status_code != SourceStatus.ACTIVE)

    session['sources.index'] = {
        'search_entry': search_entry,
        'show_finished': show_finished
    }
    return {
        'sources': sources
    }


@bp.route('/add', methods=['POST'])
@action(endpoint='sources.index')
def add():
    name = request.form['name']
    url = request.form['url']
    api_client.sources.create_from_url(name, url)


@bp.route('/start/<int:id>', methods=['POST'])
@action(endpoint='sources.index')
def start(id: int):
    api_client.sources.start(id)


@bp.route('/pause/<int:id>', methods=['POST'])
@action(endpoint='sources.index')
def pause(id: int):
    api_client.sources.pause(id)


@bp.route('/finish/<int:id>', methods=['POST'])
@action(endpoint='sources.index')
def finish(id: int):
    api_client.sources.finish(id)


@bp.route('/delete/<int:id>', methods=['POST'])
@action(endpoint='sources.index')
def delete(id: int):
    api_client.sources.delete(id)


@bp.route('/<int:id>', methods=['GET'])
@render(template='sources/source.html')
def source(id: int):
    source = api_client.sources.get(id)

    try:
        frame = api_client.sources.get_frame(id)
        frame = base64.b64encode(frame).decode('utf-8')
    except HTTPError:
        frame = None

    intervals = api_client.sources.get_time_coverage(id)
    day_coverage = {}
    for (start, end) in intervals:
        dt = datetime.fromtimestamp(start)
        day_coverage[dt.date()] = day_coverage.get(dt.date(), 0) + end - start
    if day_coverage:
        for day, count in day_coverage.items():
            cov = count / 24 / 60 / 60
            cov = cov * 0.8 + 0.2
            day_coverage[day] = cov

    calendar = []
    row = [{'day': None, 'color': None} for _ in range(7)]
    for i in range(30, -1, -1):
        dt = datetime.now() - timedelta(days=i)
        cov = day_coverage.get(dt.date(), 0)
        row[dt.weekday()]['day'] = dt.day
        row[dt.weekday()]['color'] = f'rgb{float_to_color(cov)}'
        if dt.weekday() == 6 or i == 0:
            calendar.append(row)
            row = [{'day': None, 'color': None} for _ in range(7)]

    return {
        'source': source,
        'frame': frame,
        'calendar': calendar,
    }
