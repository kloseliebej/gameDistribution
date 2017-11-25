from flask import Flask
from flask import g, request, session, redirect, url_for, render_template
import sqlite3
import config
app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    if 'user' in session:
        return 'Hello %s!' % session['user']
    else:
        return redirect(url_for('login'), 302)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        name = request.form['user']
        passwd = request.form['passwd']
        cursor = g.db.execute('select * from users where name=? and password=?', [name, passwd])
        if cursor.fetchone() is not None:
            session['user'] = name
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

@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run()
