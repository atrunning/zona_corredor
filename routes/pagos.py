from flask import Blueprint, request, redirect
from db import get_db_connection

pagos_bp = Blueprint("pagos", __name__)
