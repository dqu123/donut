from flask import Blueprint
blueprint = Blueprint('scheduler', __name__, template_folder='templates', static_folder='static')

import Donut.modules.scheduler.routes