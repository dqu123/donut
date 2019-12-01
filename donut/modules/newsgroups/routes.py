import flask 
from flask import jsonify
from donut.modules.groups import helpers as groups
from donut.modules.account import helpers as account
from donut import auth_utils

from . import blueprint, helpers

@blueprint.route('/newsgroups')
def newsgroups_home():
    if 'username' not in flask.session:
        return flask.abort(403)
    return flask.render_template(
            'newsgroups.html',
            groups=helpers.get_newsgroups())

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
            groups=helpers.get_can_send_groups(user_id),
            group_selected=group_id)

@blueprint.route('/newsgroups/postmessage', methods=['POST'])
def post_message():
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    fields = ['group', 'subject', 'msg', 'poster']
    data = {}
    for field in fields:
        data[field] = flask.request.form.get(field)
    if not data['poster']:
        user = account.get_user_data(user_id)
        data['poster'] = ' '.join([user['first_name'], user['last_name']])
    data['group_name'] = groups.get_group_data(data['group'], ['group_name'])['group_name']
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
    pos_actions = helpers.get_user_actions(user_id, group_id)
    fields = ['group_id', 'group_name', 'group_desc', 'anyone_can_send',
            'members_can_send', 'visible', 'admin_control_members']
    group_info = groups.get_group_data(group_id, fields)
    applications = None    
    if pos_actions and pos_actions['control']:
        applications = helpers.get_applications(group_id)
    
    return flask.render_template(
            'group.html',
            group=group_info,
            member=groups.is_user_in_group(user_id, group_id),
            actions=pos_actions,
            messages=helpers.get_past_messages(group_id),
            owners=helpers.get_owners(group_id),
            applications=applications)

@blueprint.route('/newsgroups/viewgroup/apply/<group_id>', methods=['POST'])
def apply_subscription(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    helpers.apply_subscription(auth_utils.get_user_id(flask.session['username']), group_id)
    flask.flash('Successfully applied for subscription')
    return flask.redirect(flask.url_for('newsgroups.view_group', group_id=group_id))

@blueprint.route('/newsgroups/viewgroup/unsub/<group_id>', methods=['POST'])
def unsubscribe(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    helpers.unsubscribe(flask.session['username'], group_id)
    flask.flash('Successfully unsubscribed')
    return flask.redirect(flask.url_for('newsgroups.view_group', group_id=group_id))

@blueprint.route('/newsgroups/mygroups')
def mygroups():
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    return flask.render_template(
            'newsgroups.html',
            groups=helpers.get_my_newsgroups(user_id))

@blueprint.route('/newsgroups/viewmsg/<post_id>')
def view_post(post_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    post = helpers.get_post(post_id)
    return flask.render_template(
            'view_post.html',
            post=post)

@blueprint.route('/newsgroups/allposts/<group_id>')
def all_posts(group_id):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    group_name = groups.get_group_data(group_id, ['group_name'])['group_name']
    return flask.render_template(
            'all_posts.html',
            group_id=group_id,
            group_name=group_name,
            messages=helpers.get_past_messages(group_id, 50))

@blueprint.route('/_delete_application')
def delete_application(user_id, group_id):
    #TODO
    return flask.redirect(flask.url_for('newsgroups.view_group', group_id=group_id))

@blueprint.route('/newsgroups/positions/<int:group>')
def my_positions(group):
    if 'username' not in flask.session:
        return flask.abort(403)
    user_id = auth_utils.get_user_id(flask.session['username'])
    return flask.jsonify(helpers.get_my_positions(group, user_id))
