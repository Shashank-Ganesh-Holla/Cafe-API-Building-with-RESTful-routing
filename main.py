import random
import os
from sqlite3 import IntegrityError

from sqlalchemy.exc import IntegrityError
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Get the absolute path to the cafes.db file
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cafes.db')

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for columns in self.__table__.columns:
            dictionary[columns.name] = getattr(self, columns.name)
        return dictionary


@app.route("/")
def home():
    if not os.path.exists("cafes.db"):
        db.create_all()
    return render_template("index.html")


## HTTP GET - Read Record

@app.route("/all")
def get_all_cafe():
    all_cafes = Cafe.query.all()
    list_cafes = []
    for cafe in all_cafes:
        each_cafe = cafe.to_dict()
        list_cafes.append(each_cafe)

    return jsonify(cafes=list_cafes)


@app.route("/search")
def search_cafe():
    search_location = request.args.get('loc')
    location_query = Cafe.query.filter_by(location=search_location.title()).all()
    # print(location_query)
    # print(len(location_query))

    if len(location_query) == 0:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})
    elif len(location_query) > 1:
        list_cafes = []
        for cafe in location_query:
            each_cafe = cafe.to_dict()
            list_cafes.append(each_cafe)
        return jsonify(cafes=list_cafes)
    else:
        return jsonify(cafe=location_query[0].to_dict())


@app.route("/random")
def get_random_cafe():
    cafes = db.session.query(Cafe).all()
    # cafes = Cafe.query.all()
    # print(cafes)
    random_cafe = random.choice(cafes)
    print(random_cafe)
    return jsonify(cafe=random_cafe.to_dict())


def str_to_bool(arg_from_url):
    if arg_from_url in ['True', ' true', 'T', 't', 'Yes', 'yes', 'y', '1']:
        return True
    else:
        return False


## HTTP POST - Create Record
@app.route('/add', methods=["GET", "POST"])
def post_new_cafe():
    try:
        cafe = Cafe(name=request.form.get('name'),
                    map_url=request.form.get('map_url'),
                    img_url=request.form.get('img_url'),
                    location=request.form.get('loc'),
                    seats=request.form.get('seats'),
                    has_toilet=str_to_bool(request.form.get('toilet')),
                    has_wifi=str_to_bool(request.form.get('wifi')),
                    has_sockets=str_to_bool(request.form.get('sockets')),
                    can_take_calls=str_to_bool(request.form.get('calls')),
                    coffee_price=request.form.get('coffee_price'),
                    )
        db.session.add(cafe)
        db.session.commit()
        return jsonify(success={"success": "Successfully added the new cafe"}), 200

    except (Exception, IntegrityError) as error:
        print(repr(error))
        print(50 * '*')
        db.session.rollback()
        error_string = repr(error)
        if "NOT NULL constraint failed" in error_string:
            return jsonify(error={"error": "Missing input parameters"}), 400

        elif "UNIQUE constraint failed" in error_string:
            return jsonify(error={"error": "Duplicate entry"}), 400
        else:
            return jsonify(error={'error': 'Error writing to database'}), 400


## HTTP PUT/PATCH - Update Record
@app.route('/update-price/<cafe_id>', methods=['PATCH'])
def update_cafe(cafe_id):
    new_price = request.args.get('new_price')
    cafe_by_id = Cafe.query.get(cafe_id)
    print(cafe_by_id)
    try:
        if cafe_by_id:
            cafe_by_id.coffee_price = new_price
            db.session.commit()
            return jsonify({"success": "Successfully updated the price"}), 200
        return jsonify(error={"Not Found": "Sorry a cafe with that id is not found in the database"}), 400
    except Exception as error:
        print(repr(error))
        return jsonify(error={"Database error": "Error updating Database "}), 500


## HTTP DELETE - Delete Record
@app.route('/report-closed/<cafe_id>', methods=['DELETE'])
def delete_cafe(cafe_id):
    key = "TopSecretAPIKey"
    requested_key = request.form.get('api-key')

    if key != requested_key:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403
    else:
        id_cafe = cafe_id
        cafe_to_delete = db.session.query(Cafe).get(id_cafe)
        if not cafe_to_delete:
            return jsonify(error={"Not Found": "Sorry a cafe with that id is not found in the database"}), 404
        else:
            try:
                db.session.delete(cafe_to_delete)
                db.session.commit()
                return jsonify(response={"Success": "Cafe successfully deleted"})
            except Exception as error:
                print(repr(error))
                return jsonify({"error": repr(error)}), 500


if __name__ == '__main__':
    app.run(debug=True)
