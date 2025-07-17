import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def load_json_response(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/blackrock/challenge/v1/transactions:parse", methods=["POST"])
def parse_transactions():
    return jsonify(load_json_response("responses/transactions_parse.json"))

@app.route("/blackrock/challenge/v1/transactions:validator", methods=["POST"])
def validate_transactions():
    return jsonify(load_json_response("responses/transactions_validator.json"))

@app.route("/blackrock/challenge/v1/transactions:filter", methods=["POST"])
def filter_transactions():
    return jsonify(load_json_response("responses/transactions_filter.json"))

@app.route("/blackrock/challenge/v1/returns:ppr", methods=["POST"])
def returns_ppr():
    return jsonify(load_json_response("responses/returns_ppr.json"))

@app.route("/blackrock/challenge/v1/performance", methods=["GET"])
def performance():
    return jsonify(load_json_response("responses/performance.json"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
