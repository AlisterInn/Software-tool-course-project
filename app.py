from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


with app.app_context():
    db.create_all()


# -- Health check
@app.route("/")
def health():
    return jsonify({"status": "ok"})


# -- List all items
@app.route("/items", methods=["GET"])
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])


# -- Get a single item
@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = db.get_or_404(Item, item_id)
    return jsonify(item.to_dict())


# -- Create an item
@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json(silent=True)
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    item = Item(name=data["name"], description=data.get("description"))
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


# -- Update an item
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = db.get_or_404(Item, item_id)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "no data provided"}), 400
    if "name" in data:
        item.name = data["name"]
    if "description" in data:
        item.description = data["description"]
    db.session.commit()
    return jsonify(item.to_dict())


# -- Delete an item
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = db.get_or_404(Item, item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Item {item_id} deleted"})


if __name__ == "__main__":
    app.run(debug=True)
