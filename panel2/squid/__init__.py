from flask import Blueprint
squid = Blueprint('squid', __name__, template_folder='templates')

import panel2.squid.models
#import panel2.squid.views
