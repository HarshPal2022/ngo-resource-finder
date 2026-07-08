from flask import Flask, jsonify
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def home():
    return jsonify({
        "project": "NGOConnect AI",
        "status": "Running",
        "version": "1.0.0"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


if __name__ == "__main__":
    app.run(debug=True)