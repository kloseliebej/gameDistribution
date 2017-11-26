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
            return render_template('developer_profile.html', session=session)
    else:
        return redirect(url_for('login'), 302)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        passwd = request.form['passwd']
        cursor = g.db.execute('select * from users where email=? and password=?', [email, passwd])
        data = cursor.fetchone()
        if data is not None:
            session['user'] = data[1]
            session['userID'] = data[0]
            session['email'] = data[3]
            session['password'] = data[2]
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
        users = g.db.execute('select * from users').fetchall()
        if cursor.fetchone() is None:
            session['user'] = name
            session['user_type'] = request.form['type']
            session['userID'] = users[-1][0]+1
            session['email'] = email
            session['password'] = passwd
            print "signup succesfully!"
            g.db.execute('insert into users (name, password, email, isGamer, isDeveloper, isManager) values (?,?,?,?,?,0)',
                         [name, passwd, email, isGamer , isDeveloper])
            g.db.commit()
            return redirect(url_for('index'))
        else:
            print "user already exist!"
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html')

@app.route('/bankaccount', methods=['POST', 'GET'])
def bankaccount():
    if request.method == 'POST':
        accountID = request.form['accountID']
        routingID = request.form['routingID']
        address = request.form['address']
        name = request.form['name']
        isDefault = 1 if request.form['isDefault'] else 0
        cursor = g.db.execute('select * from bank_account where accountID=?', [accountID])
        if cursor.fetchone() is None:
            print 'insert new bank account'
            g.db.execute('insert into bank_account (accountID, routingID, address, name, userID, isDefault) '
                         'values (?,?,?,?,?,?)',
                        [accountID, routingID, address, name, session['userID'], isDefault])
            g.db.commit()
        else:
            print "account number already exists!"
            return redirect(url_for('bankaccount'))

        return redirect(url_for('bankaccount'))
    else:
        cursor = g.db.execute('select accountID, routingID, isDefault from bank_account where userID=?',
                              [session['userID']])
        accounts = cursor.fetchall()
        return render_template('bank_account.html', accounts=accounts)

@app.route('/security', methods=['POST','GET'])
def security():
    if request.method == 'POST':
        if 'email' in request.form:
            newemail = request.form['email']

        if 'password' in request.form:
            newpwd = request.form['password']
    else:
        return render_template('security.html', session=session)

@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run()
