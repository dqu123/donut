import flask
import json

from donut.modules.marketplace import blueprint, helpers

@blueprint.route('/marketplace')
def marketplace():
    """Display marketplace page."""
    return flask.render_template('marketplace.html')

@blueprint.route('/marketplace/')
def query(category_id, query):
    """Displays all results for the query in category category_id, which can be
       'all' if no category is selected."""
    category_id = flask.request.args['c']
    query = flask.request.args['q']
    if category_id == "all":
        return helpers.render_top_marketplace_bar('search.html', cat_id=category_id)
    else:
        try:
            cat_id_num = int(category_id)
            return helpers.render_top_marketplace_bar('search.html', cat_id=category_id)
        except ValueError:
            return flask.render_template('404.html')


@blueprint.route('/1/marketplace_items')
def get_marketplace_items_list():
    """GET /1/marketplace_items/"""
    # Create a dict of the passed in attributes which are filterable
    filterable_attrs = ["item_id", "cat_id", "user_id", "item_title",
            "item_details", "item_images", "item_condition",
            "item_price", "item_timestamp", "item_active",
            "textbook_id", "textbook_isbn", "textbook_version"]
    attrs = { tup:flask.request.args[tup]
            for tup in flask.request.args if tup in filterable_attrs }
    # Get the fields to return if they were passed in
    fields = None
    if "fields" in flask.request.args:
        fields = [f.strip() for f in flask.request.args["fields"].split(',')]

    return json.dumps(helpers.get_marketplace_items_list_data(fields=fields, attrs=attrs))

