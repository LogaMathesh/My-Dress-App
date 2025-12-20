from flask import Blueprint, request
from .service import classify_image_service

classify_bp = Blueprint("classify", __name__)

@classify_bp.route("/classify", methods=["POST"])
def classify():
    return classify_image_service(request)
