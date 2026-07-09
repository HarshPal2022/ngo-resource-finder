from flask import Blueprint, jsonify, request

from database.db import (
    get_all_ngos,
    get_ngo_by_id,
    get_districts,
    search_ngos,
)

from utils.recommender import recommend

ngo_bp = Blueprint("ngo", __name__)


@ngo_bp.route("/api/ngos", methods=["GET"])
def all_ngos():

    ngos = get_all_ngos()

    return jsonify({
        "success": True,
        "count": len(ngos),
        "results": ngos
    })


@ngo_bp.route("/api/ngos/<int:ngo_id>", methods=["GET"])
def ngo_details(ngo_id):

    ngo = get_ngo_by_id(ngo_id)

    if ngo is None:

        return jsonify({
            "success": False,
            "message": "NGO not found."
        }), 404

    return jsonify({
        "success": True,
        "ngo": ngo
    })


@ngo_bp.route("/api/districts", methods=["GET"])
def districts():

    districts = get_districts()

    return jsonify({
        "success": True,
        "count": len(districts),
        "districts": districts
    })


@ngo_bp.route("/api/search", methods=["GET"])
def search():

    keyword = request.args.get("q", "").strip()
    district = request.args.get("district", "").strip()

    ngos = search_ngos(keyword, district)

    return jsonify({
        "success": True,
        "query": keyword,
        "district": district,
        "count": len(ngos),
        "results": ngos
    })


@ngo_bp.route("/api/recommend", methods=["POST"])
def recommendation():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "JSON body required."
        }), 400

    query = data.get("query", "").strip()
    district = data.get("district", "").strip()

    if query == "":

        return jsonify({
            "success": False,
            "message": "Query cannot be empty."
        }), 400

    try:

        results = recommend(query, district)

        return jsonify({
            "success": True,
            "query": query,
            "district": district,
            "count": len(results),
            "results": results
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
