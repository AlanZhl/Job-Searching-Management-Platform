from flask import Blueprint, render_template, request, session, redirect
from app.utils import checkByEmail, checkByName, checkExistence, create_userinfo
from app.models import db, Users, Permissions
from app.common import permission_check


users = Blueprint("users", __name__)


@users.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        role = request.form["role"]
        email = request.form["email"]
        password = request.form["password"]

        # post-check on the request form
        errors = checkExistence(name, email)
        if role == "":
            errors.append("Role of the user must be specified.")
        
        if len(errors) > 0:
            return render_template("register.html", errors=errors)
        else:
            newUser = Users(name=name, role=role, email=email, password=password)
            db.session.add(newUser)
            db.session.commit()
            db.session.close()
            return redirect("/login")
    else:
        return render_template("register.html")


# accessing the login page would automatically log out the current user!
@users.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        mode = request.form["mode"]
        identity = request.form["identity"]
        password = request.form["password"]

        errors = []
        if mode == "name":
            errors.extend(checkByName(identity, password))
        else:
            errors.extend(checkByEmail(identity, password))

        if len(errors) > 0:
            return render_template("login.html", errors=errors)
        user = Users.query.filter_by(name=identity).first() if mode == "name" else Users.query.filter_by(email=identity).first()
        session["user_id"] = user.user_id
        session["user_name"] = user.name
        return redirect("/")
    else:
        if session.get("user_id"): session.clear()
        return render_template("login.html")


@users.route("/user_manage", methods=["POST", "GET"])
@permission_check(Permissions.USER_MANAGE)
def user_manage():
    # for the sake of safety and privacy, users' info are not stored in sessions
    raw_users = Users.query.all()
    users = []
    for user in raw_users:
        users.append(create_userinfo(user))
    if request.method == "POST":
        try:
            request_content = request.form
            print(request_content)
            operated_users = []
            # case 1: search (exact match)
            if "keyword" in request_content.keys():
                field, val = request_content.get("search_kw"), request_content["keyword"]
                if field:
                    if field == "userid":
                        val = int(val)
                    for user in users:
                        if user.get(field) == val:
                            operated_users.append(user)
                return render_template("user_manage.html", users=operated_users, name=session.get("user_name"))
            # case 2: delete a user
            elif "delete" in request_content.keys():
                idx = int(request_content["delete"]) - 1
                user = users[idx]
                record = Users.query.filter_by(user_id=user["user_id"]).first()
                users.pop(idx)
                db.session.delete(record)
                db.session.commit()
                db.session.close()
                return render_template("user_manage.html", users=users, name=session.get("user_name"))
            # TODO: case 3: filter or sort the current user list
            else:
                return render_template("user_manage.html", users=users, name=session.get("user_name"))
        except Exception as e:
            print(e)
    return render_template("user_manage.html", users=users, name=session.get("user_name"))