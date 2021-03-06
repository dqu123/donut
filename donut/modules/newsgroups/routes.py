import flask
from flask import jsonify
from donut.modules.groups import helpers as groups
from donut.modules.account import helpers as account
from donut.modules.core.helpers import get_name_and_email
from donut import auth_utils
import html2text

from . import blueprint, helpers

# Set up converter for html to plain text
html2plain = html2text.HTML2Text()


@blueprint.route('/newsgroups')
def newsgroups_home():
    if 'username' not in flask.session:
        return flask.abort(403)
    return flask.render_template(
        'newsgroups.html', groups=helpers.get_newsgroups(), page="all")


@blueprint.route('/newsgroups/post')
@blueprint.route('/newsgroups/post/<group_id>')
def post(group_id=None):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    if not group_id:
        group_id = flask.request.form.get('group')
    return flask.render_template(
        'post.html',
        groups=helpers.get_my_newsgroups(user_id, True),
        group_selected=group_id,
        page='post')


@blueprint.route('/newsgroups/postmessage', methods=['POST'])
def post_message():
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    fields = ['group', 'subject', 'msg', 'poster']
    data = {}
    for field in fields:
        data[field] = flask.request.form.get(field)
    group_id = data['group']
    actions = helpers.get_user_actions(user_id, group_id)
    if not actions['send']:
        return flask.abort(403)
    data['group_name'] = groups.get_group_data(group_id,
                                               ['group_name'])['group_name']
    full_name = get_name_and_email(user_id)['full_name']
    poster = data['poster']
    if poster is None:
        # If not posting from a position, just use the user's name
        data['poster'] = full_name
    else:
        # If positing from a position, ensure the user has that position
        poster = int(poster)
        pos_name = None
        for position in helpers.get_posting_positions(group_id, user_id):
            if position['pos_id'] == poster:
                pos_name = position['pos_name']
                break
        if pos_name is None:
            flask.abort(403)
        data['poster'] = f'{pos_name} ({full_name})'
    data['plain'] = html2plain.handle(data['msg'])
    if helpers.send_email(data):
        flask.flash('Email sent')
        helpers.insert_email(user_id, data)
    else:
        flask.flash('Email failed to send')
    return flask.redirect(flask.url_for('newsgroups.post'))


@blueprint.route('/newsgroups/viewgroup/<group_id>')
def view_group(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    actions = helpers.get_user_actions(user_id, group_id)
    fields = [
        'group_id', 'group_name', 'group_desc', 'anyone_can_send', 'visible',
        'admin_control_members'
    ]
    group_info = groups.get_group_data(group_id, fields)
    applications = None
    if actions['control']:
        applications = helpers.get_applications(group_id)
    messages = None
    member = groups.is_user_in_group(user_id, group_id)
    if member:
        messages = helpers.get_past_messages(group_id)
    return flask.render_template(
        'group.html',
        group=group_info,
        member=member,
        actions=actions,
        messages=messages,
        owners=helpers.get_owners(group_id),
        applications=applications)


@blueprint.route('/newsgroups/viewgroup/apply/<group_id>', methods=['POST'])
def apply_subscription(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    helpers.apply_subscription(
        auth_utils.get_user_id(flask.session['username']), group_id)
    flask.flash('Successfully applied for subscription')
    return flask.redirect(
        flask.url_for('newsgroups.view_group', group_id=group_id))


@blueprint.route('/newsgroups/viewgroup/unsub/<group_id>', methods=['POST'])
def unsubscribe(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    helpers.unsubscribe(
        auth_utils.get_user_id(flask.session['username']), group_id)
    flask.flash('Successfully unsubscribed')
    return flask.redirect(
        flask.url_for('newsgroups.view_group', group_id=group_id))


@blueprint.route('/newsgroups/mygroups')
def mygroups():
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    return flask.render_template(
        'newsgroups.html',
        groups=helpers.get_my_newsgroups(user_id),
        page="my")


@blueprint.route('/newsgroups/viewmsg/<post_id>')
def view_post(post_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    post = helpers.get_post(post_id)
    if not groups.is_user_in_group(user_id, post['group_id']):
        return flask.abort(403)
    return flask.render_template('view_post.html', post=post)


@blueprint.route('/newsgroups/allposts/<group_id>')
def all_posts(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    if not groups.is_user_in_group(user_id, group_id):
        return flask.abort(403)
    group_name = groups.get_group_data(group_id, ['group_name'])['group_name']
    return flask.render_template(
        'all_posts.html',
        group_id=group_id,
        group_name=group_name,
        messages=helpers.get_past_messages(group_id, 50))


@blueprint.route('/_delete_application/<user_id>/<group_id>')
def delete_application(user_id, group_id):
    username = flask.session.get('username')
    if username is None or not helpers.get_user_actions(
            auth_utils.get_user_id(username), group_id)['control']:
        return flask.abort(403)
    helpers.remove_application(user_id, group_id)
    return flask.redirect(
        flask.url_for('newsgroups.view_group', group_id=group_id))


@blueprint.route('/newsgroups/positions/<int:group_id>')
def posting_positions(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    return flask.jsonify(helpers.get_posting_positions(group_id, user_id))
