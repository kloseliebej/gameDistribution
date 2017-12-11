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
        if 'search' in request.form:
            query = request.form['search']
            session['store-name'] = query
        elif 'store-name' in request.form:
            store_name = request.form['store-name']
            session['store-name'] = store_name
        return redirect(url_for('index'))
    else:
        games = []
        if 'store-name' not in session or session['store-name'] == "Store":
            cursor = g.db.execute('SELECT games.name, discount, price, users.name, publishDate, games.gameID '
                                  'FROM games JOIN users '
                                  'ON users.userID = games.developerID')
            games = cursor.fetchall()
        elif session['store-name'] == 'New Release':
            month = int(str(date.today())[5:7]) + 12 - 1
            month = str(date.today())[:5] + "%02d" % (month % 12) + str(date.today())[7:]
            print month
            cursor = g.db.execute('SELECT games.name, discount, price, users.name, publishDate, games.gameID '
                                  'FROM games JOIN users '
                                  'ON users.userID = games.developerID '
                                  'WHERE publishDate > ?', [month])
            games = cursor.fetchall()
        elif session['store-name'] == "Best Seller":
            cursor = g.db.execute('SELECT p.name, discount, price, users.name, publishDate, p.gameID, copies '
                                  'FROM '
                                  '(SELECT name, discount, price, publishDate, developerID, games.gameID, COUNT(*) AS copies '
                                  'FROM games JOIN transactions '
                                  'ON transactions.gameID = games.gameID '
                                  'GROUP BY games.gameID) AS p '
                                  'JOIN users '
                                  'ON users.userID = p.developerID '
                                  'ORDER BY p.copies DESC LIMIT 100')
            games = cursor.fetchall()
        elif session['store-name'] == "High Rating":
            cursor = g.db.execute(
                'SELECT p.name, discount, price, developer, publishDate, p.gameID, AVG(reviews.rating) AS rate '
                'FROM '
                '(SELECT games.name, discount, price, publishDate, users.name AS developer, games.gameID '
                'FROM games JOIN users '
                'ON users.userID = games.developerID) AS p '
                'JOIN reviews '
                'ON reviews.gameID = p.gameID '
                'GROUP BY p.gameID '
                'ORDER BY rate DESC '
                'LIMIT 100'
            )
            games = cursor.fetchall()
        elif session['store-name'] == "On Sale":
            cursor = g.db.execute(
                'SELECT games.name, discount, price, users.name, publishDate, games.gameID '
                'FROM games JOIN users '
                'ON users.userID = games.developerID '
                'WHERE discount < 100 '
                'ORDER BY discount ASC'
            )
            games = cursor.fetchall()
        else:
            cursor = g.db.execute(
                'SELECT games.name, discount, price, users.name, publishDate, games.gameID '
                'FROM games JOIN users '
                'ON users.userID = games.developerID '
                'WHERE games.name LIKE ? ', ['%' + session["store-name"] + '%']
            )
            games = cursor.fetchall()
        cursor = g.db.execute('SELECT games.name FROM games '
                              'JOIN transactions ON transactions.userID = ?'
                              'AND transactions.gameID = games.gameID', [session['userID']])
        owned = cursor.fetchall()
        names = set()
        for o in owned:
            names.add(o[0])
        data_list = []
        for game in games:
            d = {
                'name': game[0],
                'discount': game[1] - 100,
                'price': game[2],
                'developer': game[3],
                'releasedate': game[4],
                'gameID': game[5],
                'genres': [],
                'year': game[4][:4]
            }
            if session['store-name'] == "Best Seller":
                d['copies'] = game[6]
            if session['store-name'] == "High Rating":
                d['rating'] = game[6]
            if game[0] in names:
                d['addtocart'] = False
            else:
                d['addtocart'] = True
            cursor = g.db.execute('SELECT genre FROM genres WHERE gameID = ?', [d['gameID']])
            genres = cursor.fetchall()
            for genre in genres:
                d['genres'].append(genre[0])
            data_list.append(d)
        print session
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
            cursor = g.db.execute(
                'SELECT owned.gameID, owned.name, owned.date, reviews.comment, reviews.rating FROM'
                '(SELECT games.name, transactions.date, games.gameID FROM games '
                'JOIN transactions ON transactions.gameID = games.gameID '
                'AND transactions.userID = ?) AS owned '
                'LEFT JOIN reviews ON owned.gameID = reviews.gameID', [session['userID']]
            )
            games = cursor.fetchall()
            print games
            data_list = []
            for game in games:
                d = {}
                d['gameID'] = game[0]
                d['name'] = game[1]
                d['purchaseDate'] = game[2]
                if game[3]:
                    d['reviews'] = "\"" + game[3] + "\", (" + str(game[4]) + ") stars "
                data_list.append(d)
            return render_template('gamer_profile.html', session=session, games=data_list)
        else:
            cursor = g.db.execute(
                'SELECT games.name, games.publishDate, AVG(reviews.rating), COUNT(transactions.gameID) AS saleNum,'
                'COUNT(transactions.gameID) * games.discount * games.price / 100 AS income, games.discount, games.gameID '
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
                     'discount': game[5] - 100,
                     'gameID': game[6],
                     'genres': []
                     }
                cursor = g.db.execute('SELECT genre FROM genres WHERE gameID = ?', [game[6]])
                genres = cursor.fetchall()
                for genre in genres:
                    d['genres'].append(genre[0])
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
    print gameID
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
        data = {'gameID': gameID}
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
        d = request.form['date']
        print d, type(d)
        g.db.execute('INSERT INTO games (name, discount, price, developerID, publishDate) '
                     'VALUES (?,?,?,?,?)', [name, discount, price, uid, d])
        g.db.commit()
        return redirect(url_for('profile'))
    else:
        return render_template('upload.html', session=session)


@app.route('/add-to-cart/<int:gameID>')
def add_to_cart(gameID):
    if 'cart' not in session:
        session['cart'] = [gameID]
    elif gameID not in session['cart']:
        session['cart'] = session['cart'] + [gameID]
    print gameID, session['cart']
    return redirect(url_for('index'))


@app.route('/cart', methods=['POST', 'GET'])
def checkout():
    if request.method == 'POST':
        for gameID in session['cartgameID']:
            date_str = str(date.today())
            g.db.execute('INSERT INTO transactions (date, gameID, userID) '
                         'VALUES (?,?,?)', [date_str, gameID, session['userID']])
            g.db.commit()
        session.pop('cart')
        session.pop('cartgameID')
        return redirect(url_for('profile'))
    else:
        data_list = []
        gameID_list = []
        price = 0
        for gameID in session['cart']:
            cursor = g.db.execute('SELECT name, discount, price, gameID FROM games WHERE gameID = ?', [gameID])
            game = cursor.fetchone()
            d = {'name': game[0],
                 'discount': game[1] - 100,
                 'price': int(game[1] * game[2] / 100.0),
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


@app.route('/show-single/<int:gameID>')
def show_single(gameID):
    cursor = g.db.execute(
        'SELECT name, discount, price, publishDate, copies, AVG(reviews.rating) FROM '
        '(SELECT name, discount, price, publishDate, COUNT(*) AS copies, games.gameID '
        'FROM games LEFT JOIN transactions ON games.gameID = transactions.gameID '
        'AND games.gameID = ? '
        'GROUP BY games.gameID) AS p '
        'LEFT JOIN reviews ON reviews.gameID = p.gameID', [gameID]
    )
    game = cursor.fetchone()
    print game
    gid = gameID
    d = {
        'name': game[0],
        'price': game[2],
        'discount': game[1] - 100,
        'date': game[3],
        'gameID': gid,
        'copies': game[4],
        'avg': game[5],
        'genres': [],
        'reviews': []
    }
    cursor = g.db.execute('SELECT genre FROM genres WHERE gameID = ?', [gid])
    genres = cursor.fetchall()
    for genre in genres:
        d['genres'].append(genre[0])
    cursor = g.db.execute('SELECT comment, rating FROM reviews WHERE gameID = ?', [gid])
    reviews = cursor.fetchall()
    for review in reviews:
        d['reviews'].append({
            'comment': review[0],
            'rating': review[1]
        })
    return render_template('show_single.html', session=session, game=d)


@app.route('/add-genre/<int:gameID>', methods=['POST', 'GET'])
def add_genre(gameID):
    if request.method == 'POST':
        uid = session['userID']
        genre = request.form['genre']
        g.db.execute('INSERT INTO genres (genre, gameID) '
                     'VALUES (?,?)', [genre, gameID])
        g.db.commit()
        return redirect(url_for('profile'))
    else:
        data = {"gameID": gameID}
        return render_template('add_genre.html', session=session, game=data)


@app.route('/show-reviews/<int:gameID>')
def show_reviews(gameID):
    cursor = g.db.execute('SELECT comment, rating FROM reviews WHERE gameID = ?', [gameID])
    reviews = cursor.fetchall()
    d = {
        'reviews': []
    }
    for review in reviews:
        d['reviews'].append({
            'comment': review[0],
            'rating': review[1]
        })
    return render_template('show_reviews.html', session=session, game=d)


@app.route('/sale-report', methods=['POST', 'GET'])
def sale_report():
    if request.method == 'POST':
        start = request.form['start']
        end = request.form['end']
        sort_type = request.form['type']
        cursor = g.db.execute(
            'SELECT name, COUNT(*) AS copies, price * COUNT(*) * discount AS income '
            'FROM games JOIN transactions '
            'ON games.gameID = transactions.gameID '
            'WHERE transactions.date > ? AND transactions.date < ?'
            'GROUP BY games.gameID ORDER BY ? ASC ', [start, end, sort_type]
        )
        games = cursor.fetchall()
        data_list = []
        for game in games:
            d = {}
            d['name'] = game[0]
            d['copies'] = game[1]
            d['income'] = game[2] / 100.0
            data_list.append(d)
        print data_list, sort_type
        return render_template('sale_report.html', session=session, games=data_list)
    else:
        return render_template("sale_report.html", session=session, games={})


@app.route('/top-developer', methods=['POST', 'GET'])
def top_developer():
    if request.method == 'POST':
        start = request.form['start']
        end = request.form['end']
        sort_type = request.form['type']
        cursor = g.db.execute(
            'SELECT developerID, COUNT(*) AS copies, SUM(price * discount) AS income '
            'FROM games JOIN transactions '
            'ON games.gameID = transactions.gameID '
            'WHERE transactions.date > ? AND transactions.date < ?'
            'GROUP BY games.developerID ORDER BY ? DESC ', [start, end, sort_type]
        )
        devs = cursor.fetchall()
        data_list = []
        for dev in devs:
            d = {}
            d['name'] = dev[0]
            d['copies'] = dev[1]
            d['income'] = dev[2] / 100.0
            data_list.append(d)
        print data_list
        return render_template('top_developer.html', session=session, devs=data_list)
    else:
        return render_template("top_developer.html", session=session, devs={})


@app.route('/popular-genre', methods=['POST', 'GET'])
def popular_genre():
    if request.method == 'POST':
        start = request.form['start']
        end = request.form['end']
        sort_type = request.form['type']
        cursor = g.db.execute(
            'SELECT genre, SUM(g.copies) AS copies, SUM(g.copies * g.p) AS income FROM '
            '(SELECT games.gameID, COUNT(*) AS copies, price * discount AS p, transactions.date '
            'FROM games JOIN transactions '
            'ON games.gameID = transactions.gameID '
            'GROUP BY games.gameID) AS g '
            'JOIN genres ON g.gameID = genres.gameID '
            'WHERE g.date > ? AND g.date < ? '
            'GROUP BY genre ORDER BY ? DESC ', [start, end, sort_type]
        )
        print sort_type, start, end
        gs = cursor.fetchall()
        data_list = []
        for genre in gs:
            d = {}
            d['name'] = genre[0]
            d['copies'] = genre[1]
            d['income'] = genre[2] / 100.0
            data_list.append(d)
        print data_list
        return render_template('popular_genre.html', session=session, genres=data_list)
    else:
        return render_template("popular_genre.html", session=session, genres={})


@app.route('/update-discount/<int:gameID>', methods=['POST'])
def update_discount(gameID):
    discount = int(request.form['new-discount'])
    g.db.execute('UPDATE games SET discount=? WHERE gameID=?', [discount, gameID])
    g.db.commit()
    return redirect(url_for('profile'))

@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


if __name__ == '__main__':
    app.run()
