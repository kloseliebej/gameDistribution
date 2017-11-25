from flask import Flask
from flask import g, request, session, redirect, url_for, render_template
import sqlite3
import config
app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    if 'user' in session:
        print session
        if session['user_type'] == 'manager':
            return render_template('manager_profile.html', session=session)
        elif session['user_type'] == 'gamer':
            return render_template('manager_profile.html', session=session)
        else:
            return render_template('manager_profile.html', session=session)
    else:
        return redirect(url_for('login'), 302)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        name = request.form['user']
        passwd = request.form['passwd']
        cursor = g.db.execute('select * from users where name=? and password=?', [name, passwd])
        data = cursor.fetchone()
        if data is not None:
            session['user'] = name
            if data[4] == 1:
                session['user_type'] = 'gamer'
            elif data[5] == 1:
                session['user_type'] = 'developer'
            else:
                session['user_type'] = 'manager'
            print 'Login successfully!'
            return redirect(url_for('index'))
        else:
            print 'No such user!', 'error'
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        passwd = request.form['passwd']
        if request.form['type']=='gamer':
            isGamer = 1
            isDeveloper = 0
        else:
            isDeveloper = 1
            isGamer = 0
        cursor = g.db.execute('select * from users where email=?', [email])
        if cursor.fetchone() is None:
            session['user'] = name
            session['user_type'] = request.form['type']
            print "signup succesfully!"
            g.db.execute('insert into users (name, password, email, isGamer, isDeveloper, isManager) values (?,?,?,?,?,0)',
                         [name, passwd, email, isGamer , isDeveloper])
            return redirect(url_for('index'))
        else:
            print "user already exist!"
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html')

@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run()
