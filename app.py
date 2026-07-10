from flask import Flask, render_template, jsonify

from routes.ngo_routes import ngo_bp

app = Flask(__name__)

app.register_blueprint(ngo_bp)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "project": "NGOConnect AI"
    })

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False)