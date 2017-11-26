from flask import Flask
from flask import g, request, session, redirect, url_for, render_template
import sqlite3

from gameDistribution import app

@app.route('/payment')
def show_payment():
    cursor = g.db.execute('SELECT cardID, expDate from payment_information '
                         'WHERE userID = ?', [session['userID']])
    cards = cursor.fetchall()
    print cards
    data_list = []
    for card in cards:
        d = {}
        d['cardID'] = card[0]
        d['last'] = card[0] % 10000
        d['exp'] = card[1]
    print data_list
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