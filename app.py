from flask import Flask, request, redirect, url_for, render_template

from airtable import Airtable

from dotenv import load_dotenv

import os

import urllib

from urllib.request import urlopen, Request

import ast

import json

from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("KEY")  # Change this!

users_table = Airtable(os.getenv("AIRTABLE_BASE"),
                       'Users', os.getenv("AIRTABLE_KEY"))


entry_table = Airtable(os.getenv("AIRTABLE_BASE"),
                       'Entries', os.getenv("AIRTABLE_KEY"))


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/checkin', methods=['GET', 'POST'])
def checkin():

    if len(users_table.search('ID Number', request.form['idNumber'])) == 0:
        return render_template('moreinfo.html', idNumber=request.form['idNumber'], storeID=request.form['storeID'])

    userID = users_table.search('ID Number', request.form['idNumber'])[0]["fields"]["User ID"]
    record = entry_table.match("Related Main Field", userID, sort='-Entrance Time')
    
    if record != {}:
    
        if record["fields"]["Exit Time Forced"] == 1:
        
            entry_table.update_by_field('Entry Record ID', record["fields"]["Entry Record ID"], {'Exit Time': str(datetime.now())})
            
            contacts = entry_table.get_all(filterByFormula="AND(OR(" +
                    'AND(IS_AFTER({Entrance Time},"' +
                    str(record["fields"]["Entrance Time"]) +
                    '"),IS_BEFORE({Entrance Time},"' +
                    str(datetime.now()) +
                    '")),' +
                    'AND(IS_AFTER({Exit Time},"' +
                    str(record["fields"]["Entrance Time"]) +
                    '"),IS_BEFORE({Exit Time},"' +
                    str(datetime.now()) +
                    '")),' +
                    'AND(IS_AFTER({Exit Time},"' +
                    str(record["fields"]["Entrance Time"]) +
                    '"),IS_BEFORE({Exit Time},"' +
                    str(datetime.now()) +
                    '")),' +
                    'AND(IS_BEFORE({Entrance Time},"' +
                    str(record["fields"]["Entrance Time"]) +
                    '"),IS_AFTER({Exit Time},"' +
                    str(datetime.now()) +
                    '")),' +
                    'AND(IS_SAME({Entrance Time},"' +
                    str(record["fields"]["Entrance Time"]) +
                    '")),' +
                    'AND(IS_SAME({Exit Time},"' +
                    str(datetime.now()) +
                    '"))),IF({Persons ID}!="' +
                    str(record["fields"]["Persons ID"]) +
                    '",TRUE(),FALSE()))',)
            contactsID =[]
            for i in contacts:

                if i["fields"]["Related User"][0] != record["fields"]["Related User"][0]:

                    contactsID.append(i["fields"]["Related User"][0])

            entry_table.update_by_field('Entry Record ID', record["fields"]["Entry Record ID"], {'Contacts': contactsID})

            return render_template('donecheckout.html')

        else:
            entry_table.insert({"Related Place": [request.form['storeID']],
                    "Related User": [users_table.search('ID Number', request.form['idNumber'])[0]["id"]],
                    "Entrance Time": str(datetime.now()),})
            return render_template('donecheckin.html')
    else:
            entry_table.insert({"Related Place": [request.form['storeID']],
                    "Related User": [users_table.search('ID Number', request.form['idNumber'])[0]["id"]],
                    "Entrance Time": str(datetime.now()),})
            return render_template('donecheckin.html')
    print(request.form['idNumber'])

    return render_template('donecheckin.html')


@app.route('/registerandcheckin', methods=['GET', 'POST'])
def registerAndCheckin():

    users_table.insert({'Full Name': request.form['name'], "ID Number": request.form['idNumber'],
                        'Street Address': request.form['address'], 'Phone Number': request.form['phone']})

    entry_table.insert({"Related Place": [request.form['storeID']],
                "Related User": [users_table.search('ID Number', request.form['idNumber'])[0]["id"]],
                "Entrance Time": str(datetime.now()),})

    print(request.form['idNumber'])

    return render_template('donecheckin.html')


@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')

if __name__ == '__main__':
    from os import environ
    app.run(debug=False, host='0.0.0.0', port=environ.get("PORT", 5000))
