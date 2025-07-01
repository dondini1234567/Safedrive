from flask import Blueprint

bp = Blueprint('drive_api', __name__)

from app.drive import google_drive
