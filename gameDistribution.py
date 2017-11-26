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
            return render_template('gamer_profile.html', session=session)
        else:
            return render_template('developer_profile.html', session=session)
    else:
        return redirect(url_for('login'), 302)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        passwd = request.form['passwd']
        cursor = g.db.execute('SELECT * FROM users WHERE email=? AND password=?', [email, passwd])
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
        if request.form['type'] == 'gamer':
            isGamer = 1
            isDeveloper = 0
        else:
            isDeveloper = 1
            isGamer = 0
        cursor = g.db.execute('SELECT * FROM users WHERE email=?', [email])
        users = g.db.execute('SELECT * FROM users').fetchall()
        if cursor.fetchone() is None:
            session['user'] = name
            session['user_type'] = request.form['type']
            session['userID'] = users[-1][0] + 1
            session['email'] = email
            session['password'] = passwd
            print "signup succesfully!"
            g.db.execute(
                'INSERT INTO users (name, password, email, isGamer, isDeveloper, isManager) VALUES (?,?,?,?,?,0)',
                [name, passwd, email, isGamer, isDeveloper])
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
        cursor = g.db.execute('SELECT * FROM bank_account WHERE accountID=?', [accountID])
        if cursor.fetchone() is None:
            print 'insert new bank account'
            if isDefault == 1:
                g.db.execute('UPDATE bank_account SET isDefault=0 ')
                g.db.commit()
            g.db.execute('INSERT INTO bank_account (accountID, routingID, address, name, userID, isDefault) '
                         'VALUES (?,?,?,?,?,?)',
                         [accountID, routingID, address, name, session['userID'], isDefault])
            g.db.commit()
        else:
            print "account number already exists!"
            return redirect(url_for('bankaccount'))

        return redirect(url_for('bankaccount'))
    else:
        cursor = g.db.execute('SELECT accountID, routingID, isDefault FROM bank_account WHERE userID=?',
                              [session['userID']])
        accounts = cursor.fetchall()
        return render_template('bank_account.html', accounts=accounts)


@app.route('/security', methods=['POST', 'GET'])
def security():
    if request.method == 'POST':
        if 'email' in request.form:
            newemail = request.form['email']
            g.db.execute('UPDATE users SET email=? WHERE userID=?', [newemail, session['userID']])
            g.db.commit()
            session['email'] = newemail
            return redirect(url_for('security'))

        if 'password' in request.form:
            newpwd = request.form['password']
            g.db.execute('UPDATE users SET password=? WHERE userID=?', [newpwd, session['userID']])
            g.db.commit()
            session['password'] = newpwd
            return redirect(url_for('security'))
    else:
        return render_template('security.html', session=session)


@app.route('/games')
def user_games():
    cursor = g.db.execute('SELECT games.gameID, games.name, transactions.date, reviews.comment, reviews.rating '
                          'FROM games JOIN transactions ON transactions.userID = ? '
                          'LEFT JOIN reviews ON games.gameID = reviews.gameID', [session['userID']])
    games = cursor.fetchall()
    data_list = []
    for game in games:
        d = {}
        d['gameID'] = game[0]
        d['name'] = game[1]
        d['purchaseDate'] = game[2]
        d['reviews'] = game[3] + ", " + game[4]
        data_list.append(d)
    return render_template('games.html', session=session, games=data_list)

@app.route('/add-review/<int:gameID>', methods=['POST', 'GET'])
def add_review(gameID):
    if request.method == 'POST':
        uid = session['userID']
        gid = gameID
        comment = request.form['comment']
        rating = int(request.form['rating'])
        g.db.execute('INSERT INTO reviews (rating, comment, userID, gameID) '
                     'VALUES (?,?,?,?)', [rating, comment, uid, gid])
        g.db.commit()
        return redirect(url_for(user_games))
    else:
        data = {'gameID', gameID}
        return render_template('add_review.html', session=session, game=data)


@app.route('/payment')
def show_payment():
    cursor = g.db.execute('SELECT cardID, expDate from payment_information '
                         'WHERE userID = ?', [session['userID']])
    cards = cursor.fetchall()
    data_list = []
    for card in cards:
        d = {}
        d['cardID'] = card[0]
        d['last'] = card[0] % 10000
        d['exp'] = card[1]
        data_list.append(d)
    return render_template('payment.html', session=session, cards=data_list)


@app.route('/add-card', methods=['POST', 'GET'])
def add_card():
    if request.method == 'POST':
        uid = session['userID']
        cardID = int(request.form['cardID'])
        exp = request.form['exp']
        cvv = request.form['cvv']
        name = request.form['name']
        g.db.execute('INSERT INTO payment_information (cardID, CVV, expDate, name, userID) '
                     'VALUES (?,?,?,?,?)', [cardID, cvv, exp, name, uid])
        g.db.commit()
        return redirect(url_for('show_payment'))
    else:
        return render_template('add_card.html', session=session)


@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


if __name__ == '__main__':
    app.run()
