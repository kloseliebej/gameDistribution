from flask import Flask
from flask import g, request, session, redirect, url_for, render_template
import sqlite3
from datetime import date
import config

app = Flask(__name__)
app.config.from_object('config')


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        if 'store-name' in request.form:
            store_name = request.form['store-name']
            session['store-name'] = store_name
        return redirect(url_for('index'))
    else:
        cursor = g.db.execute('SELECT games.name, discount, price, users.name, publishDate, games.gameID '
                              'FROM games JOIN users '
                              'WHERE users.userID = games.developerID')
        games = cursor.fetchall()
        cursor = g.db.execute('SELECT games.name FROM games '
                              'JOIN transactions ON transactions.userID = ?', [session['userID']])
        owned = cursor.fetchall()
        names = set()
        for o in owned:
            names.add(o[0])
        data_list = []
        for game in games:
            d = {'name': game[0],
                 'discount': game[1],
                 'price': game[2],
                 'developer': game[3],
                 'releasedate': game[4]}
            if game[0] in names:
                d['addtocart'] = None
            else:
                d['addtocart'] = "Add to cart"
            data_list.append(d)
        if 'cart' in session:
            session['incart'] = len(session['cart'])
        else:
            session['incart'] = 0
        return render_template('main.html', session=session, games=data_list)


@app.route('/profile')
def profile():
    if 'user' in session:
        print session
        if session['user_type'] == 'manager':
            return render_template('manager_profile.html', session=session)
        elif session['user_type'] == 'gamer':
            cursor = g.db.execute('SELECT games.gameID, games.name, transactions.date, reviews.comment, reviews.rating '
                                  'FROM games JOIN transactions ON transactions.userID = ? '
                                  'LEFT JOIN reviews ON games.gameID = reviews.gameID '
                                  'AND reviews.userID = ?', [session['userID'], session['userID']])
            games = cursor.fetchall()
            data_list = []
            for game in games:
                d = {}
                d['gameID'] = game[0]
                d['name'] = game[1]
                d['purchaseDate'] = game[2]
                if game[3]:
                    d['reviews'] = game[3] + ", " + str(game[4])
                data_list.append(d)
            return render_template('gamer_profile.html', session=session, games=data_list)
        else:
            cursor = g.db.execute('SELECT games.name, games.publishDate, AVG(reviews.rating), COUNT(transactions.gameID) as saleNum,'
                                  'COUNT(transactions.gameID) * games.discount * games.price / 100 as income, games.discount '
                                  'FROM games '
                                  'LEFT JOIN transactions ON games.gameID = transactions.gameID '
                                  'LEFT JOIN reviews ON games.gameID = reviews.gameID '
                                  'WHERE games.developerID = ? GROUP BY games.gameID', [session['userID']])
            games = cursor.fetchall()
            data_list = []
            for game in games:
                d = {'name': game[0],
                     'releasedate': game[1],
                     'rating': game[2],
                     'reviews': game[2],
                     'copies': game[3],
                     'income': game[4],
                     'discount': game[5]}
                data_list.append(d)
            return render_template('developer_profile.html', session=session, games=data_list)
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
    session.pop('cart', None)
    return redirect(url_for('index'))


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
        return redirect(url_for('profile'))
    else:
        data = {'gameID', gameID}
        return render_template('add_review.html', session=session, game=data)


@app.route('/payment')
def show_payment():
    cursor = g.db.execute('SELECT cardID, expDate FROM payment_information '
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


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        uid = session['userID']
        name = request.form['name']
        price = int(request.form['price'])
        discount = int(request.form['discount'])
        d = str(date.today())
        g.db.execute('INSERT INTO games (name, discount, price, developerID, publishDate) '
                     'VALUES (?,?,?,?,?)', [name, discount, price, uid, d])
        g.db.commit()
        return redirect(url_for('profile'))
    else:
        return render_template('upload.html', session=session)


@app.route('/add-to-cart/<game_name>')
def add_to_cart(game_name):
    if 'cart' not in session:
        session['cart'] = [game_name]
    elif game_name not in session['cart']:
        session['cart'].append(game_name)
    return redirect(url_for('index'))


@app.route('/cart', methods=['POST', 'GET'])
def checkout():
    if request.method == 'POST':
        for gameID in session['cartgameID']:
            date_str= str(date.today())
            g.db.execute('INSERT INTO transactions (date, gameID, userID) '
                         'VALUES (?,?,?)', [date_str, gameID, session['userID']])
            g.db.commit()
        return redirect(url_for('profile'))
    else:
        data_list = []
        gameID_list = []
        price = 0
        for game_name in session['cart']:
            cursor = g.db.execute('SELECT name, discount, price, gameID FROM games WHERE name = ?', [game_name])
            game = cursor.fetchone()
            d = {'name': game[0],
                 'discount': game[1],
                 'price': int((100 - game[1]) * game[2]/ 100.0),
                 'gameID': game[3]}
            data_list.append(d)
            gameID_list.append(d['gameID'])
            price += d['price']
        session['cartgameID'] = gameID_list
        # card part
        cursor = g.db.execute('SELECT cardID, expDate FROM payment_information '
                              'WHERE userID = ?', [session['userID']])
        cards = cursor.fetchall()
        card_list = []
        for card in cards:
            d = {}
            d['cardID'] = card[0]
            d['last'] = card[0] % 10000
            d['exp'] = card[1]
            card_list.append(d)
        return render_template('cart.html', session=session, games=data_list, price=price, cards=card_list)


@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


if __name__ == '__main__':
    app.run()
