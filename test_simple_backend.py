#!/usr/bin/env python3
"""
Test simple du backend sans base de données
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

@app.route("/api/health", methods=["GET"])
def health():
    """Healthcheck endpoint simple"""
    return jsonify({"status": "ok"})

@app.route("/api/test", methods=["GET"])
def test():
    """Test endpoint simple"""
    return jsonify({"message": "Backend fonctionne", "version": "1.0"})

if __name__ == "__main__":
    print("Démarrage du serveur de test...")
    app.run(host="0.0.0.0", port=8001, debug=True)
