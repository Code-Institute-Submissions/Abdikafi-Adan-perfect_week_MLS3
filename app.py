import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/motivation")
def motivation():
    return render_template("motivation.html")


@app.route("/get_plans")
def get_plans():
    plans = list(mongo.db.plans.find())

    return render_template("plans.html", plans=plans)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("get_plans", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "get_plans", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# @app.route("/profile/<username>", methods=["GET", "POST"])
# def profile(username):
#     # graps the session user's username from db
#     username = mongo.db.users.find_one(
#                         {"username": session["user"]})["username"]

#     if session["user"]:
#         return render_template("profile.html", username=username)

#     return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # Loggs out User from sesion cookie
    flash("You have been  logged out ")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_plan",  methods=["GET", "POST"])
def add_plan():
    # handels the Post resquset from the form in add_plan html
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        plan = {
            "category_name": request.form.get("category_name"),
            "plan_name": request.form.get("plan_name"),
            "plan_description": request.form.get("plan_description"),
            "is_urgent": is_urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        mongo.db.plans.insert_one(plan)
        flash("Plan Successfully Added")
        return redirect(url_for("get_plans"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_plan.html", categories=categories)


@app.route("/edit_plan/<plan_id>", methods=["GET", "POST"])
def edit_plan(plan_id):
    # handels the Post resquset to upddate the form
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        edit_form = {
            "category_name": request.form.get("category_name"),
            "plan_name": request.form.get("plan_name"),
            "plan_description": request.form.get("plan_description"),
            "is_urgent": is_urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }

        mongo.db.plans.update({"_id": ObjectId(plan_id)}, edit_form)
        flash("Plan was Successfully Edited ")

    plan = mongo.db.plans.find_one({"_id": ObjectId(plan_id)})

    categories = mongo.db.categories.find().sort("category_name", -1)
    return render_template("edit_plan.html", plan=plan, categories=categories)


# Allows user to delete plan
@app.route('/delete_task/<plan_id>')
def delete_plan(plan_id):

    mongo.db.plans.remove({'_id': ObjectId(plan_id)})
    flash("Plan was Successfully Delete")

    return redirect(url_for('get_plans'))


@app.route('/get_categories')
def get_categories():
    categories = mongo.db.categories.find().sort("category_name", 1)

    return render_template("categories.html", categories=categories)


@app.route('/add_category', methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("Category was Successfully Add")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route('/edit_category/<category_id>', methods=["GET", "POST"])
def edit_category(category_id):

    if request.method == "POST":
        update = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, update)
        flash("Category was Successfully Updated")
        return redirect(url_for("get_categories"))
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route('/delete_category/<category_id>')
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category was Successfully Deleted")
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
