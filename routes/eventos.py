from flask import Blueprint
from db import get_db_connection
from layout import layout

eventos_bp = Blueprint("eventos", __name__)


