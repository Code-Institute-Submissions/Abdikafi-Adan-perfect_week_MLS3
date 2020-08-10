import os
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    session,
    flash,
    Markup
)
from bson.objectid import ObjectId
import bcrypt
from flask_pymongo import PyMongo

if os.path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config['MONGO_DBNAME'] = 'MLS-projetDB'
mongo = PyMongo(app)
tasks = mongo.db.tasks.find()
users = mongo.db.users



# show the index as the starting site and introduces the use to the website
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

# the sign in feature and routes
@app.route('/sign_in', methods=['POST', 'GET'])
def sign_in():
    if request.method == "GET":
        # If a user is already in session, they are flashed a message
        # confirming this to them, with a prompt to sign out to change account.
        if 'username' in session:
            flash(
                'You\'re already signed in! Sign out ' +
                'first if you want to change account.')
            return redirect(url_for('overview'))

        return render_template('signin.html')

    elif request.method == "POST":
        login_user = users.find_one({'name': request.form['username']})
        # This checks to see if the hashed password in the form matches the
        # hashed password in the DB and adds them to the session
        if login_user:
            if bcrypt.hashpw(request.form['pass'].encode(
                    'utf-8'), login_user['password']
                    ) == login_user['password']:
                session['username'] = request.form['username']
                # If correct, the user is sent to their personal overview
                # page with all task functions available to them. Otherwise
                # they are flashed a warning message to try again
                return redirect(url_for('overview'))
            else:
                flash(
                    'Oops, it looks like you\'ve entered the wrong' +
                    ' combination of username and password. Why not' +
                    ' try again?')
                return redirect(url_for('sign_in'))

        elif not login_user:
            flash(
                'We don\'t have that username on file! Please check' +
                ' your spelling and try again.')
            return redirect(url_for('sign_in'))


# Routing for new users to sign up, hashing the password for security
@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    if request.method == "GET":
        # If a user is already signed in, they are flashed a warning
        # message to sign out to prevent multiple sign-ins
        if 'username' in session:
            flash(
                'You\'re already signed in! Sign out first if ' +
                'you want to change account.')
            return redirect(url_for('overview'))

    else:
        # If there is no existing user in the DB, the entered password
        # is hashed for security before being sent to store in the DB
        existing_user = users.find_one({'name': request.form['username']})
        if existing_user is None:
            hashpass = bcrypt.hashpw(
                request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert(
                {'name': request.form['username'], 'password': hashpass})
            session['username'] = request.form['username']
            # With the user data stored, they are sent to their new
            # 'overview' page
            return redirect(url_for('overview'))

        flash(
            'Oops, that username already exists! ' +
            'Please try again with another username.')

    return render_template('signup.html')


# Function to logout existing users
@app.route('/logout')
def logout():
    username = session['username']
    if 'username' in session:
        # This removes session 
        session.pop('username', None)

        flash(
            "You've successfully logged out. " +
            "See you next time, " +
            username + "!")

        return redirect(url_for('sign_in'))


# Routing that shows the user's overview/ dashboard when they have signed in
# or registered
@app.route('/overview', methods=['GET', 'POST'])
def overview():
    # Redirects a user not in session to the signup page
    if 'username' not in session:
        return render_template('signup.html')

    tasks = list(mongo.db.tasks.find({"username": session["username"]}))
    # Adds completed tasks to completed list
    completed = []

    if tasks:
        for task in tasks:

            if task["complete"]:
                completed.append(task)
        return render_template(
            'overview.html',
            completed_tasks='Complete tasks:',
            tasks=tasks,
            completed=completed)

# Routing to direct users to the page where they can begin to add tasks
@app.route('/new_task')
def new_task():
    # Redirects a user not in session to the signup page
    if 'username' not in session:
        return render_template('signup.html')
    return render_template('newtasks.html')

# Function to add user tasks to the DB, collecting username from session
# to prevent user from providing it again
@app.route('/add_task', methods=['POST'])
def add_task():
    tasks = mongo.db.tasks
    username = session['username']
    form_data = {
        "username": username,
        "task_title": request.form.get("task_title"),
        "task_info": request.form.get("task_info"),
        "task_due": request.form.get("task_due"),
        "complete": False
    }
    tasks.insert_one(form_data)

    return redirect(url_for('overview'))


# Routing to direct the user to the edit task page if they are signed in
@app.route('/edit_task/<task_id>')
def edit_task(task_id):
    # Redirects a user not in session to the signup page
    if 'username' not in session:
        return render_template('signup.html')

    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    return render_template('updatetasks.html', task=task)



# Function to update a user's task
@app.route('/update_tasks/<task_id>', methods=['POST', 'GET'])
def update_tasks(task_id):
    # Redirects a user not in session to the signup page
    if 'username' not in session:
        return render_template('signup.html')
    # If user is in session continue to update the task
    username = session['username']

    if request.method == 'POST':
        updating_task = mongo.db.tasks.find_one_and_update(
            {"_id": ObjectId(task_id)},
            {"$set":
                {"username": username,
                    "task_title": request.form.get("task_title"),
                    "task_info": request.form.get("task_info"),
                    "task_due": request.form.get("task_due"),
                    "complete": False}}
        )

        flash('Success, your task has been changed!')
        return redirect(url_for('overview', task=updating_task))

    else:
        updating_task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
        return render_template('updatetasks.html', task=updating_task)


# complete plan/task features
@app.route('/complete_task/<task_id>', methods=['POST', 'GET'])
def complete_task(task_id):

    mongo.db.tasks.update(
        {'_id': ObjectId(task_id)},
        {"$set": {
            "complete": True}})

    return redirect(url_for('overview'))


# Allows user to delete plan/task 
@app.route('/delete_task/<task_id>')
def delete_task(task_id):
    mongo.db.tasks.remove({'_id': ObjectId(task_id)})

    return redirect(url_for('overview'))


# Allows a user to delete a completed task from their completed list
@app.route('/delete_complete_task/<complete_id>')
def delete_complete_task(complete_id):
    mongo.db.tasks.remove({'_id': ObjectId(complete_id)})

    flash("Your completed task has been deleted.")
    return redirect(url_for('overview'))

if __name__ == '__main__':
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)