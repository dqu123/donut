import flask
import json
from flask import jsonify

from donut.modules.core import blueprint, helpers


@blueprint.route("/1/members/")
def get_members_list():
    """GET /1/members/"""
    # Create a dict of the passed in attributes which are filterable
    filterable_attrs = [
        "uid", "last_name", "first_name", "middle_name", "email", "entry_year",
        "graduation_year", "zip"
    ]
    attrs = {
        tup: flask.request.args[tup]
        for tup in flask.request.args if tup in filterable_attrs
    }

    # Get the fields to return if they were passed in
    fields = None
    if "fields" in flask.request.args:
        fields = [f.strip() for f in flask.request.args["fields"].split(',')]

    return jsonify(helpers.get_member_list_data(fields=fields, attrs=attrs))


@blueprint.route("/1/members/<int:user_id>/")
def get_members(user_id):
    """GET /1/members/<int:user_id>/"""
    filterable_attrs = [
        "uid", "last_name", "first_name", "middle_name", "email", "entry_year",
        "graduation_year", "zip"
    ]
    
    # Get the fields to return if they were passed in
    fields = None
    if "fields" in flask.request.args:
        fields = [f.strip() for f in flask.request.args["fields"].split(',')]
    
    return json.dumps(helpers.get_member_data(user_id, fields=fields))


@blueprint.route("/1/members/<int:user_id>/groups/")
def get_group_list_of_member(user_id):
    '''GET /1/members/<int:user_id>/groups/
       List all groups that a member is in  
    '''
    return jsonify(helpers.get_group_list_of_member(user_id))
