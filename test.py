import flask
from flask import Flask, render_template,redirect,url_for,request, request, jsonify, make_response, session, flash

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dash.html',**{'name':'Abhijit'})


@app.route('/submit', methods=['POST'])
def getdata():
    if request.method == 'POST':
        data = request.form
        print(data['Name'])
        return data['Name']
    return 'not submitted'


if __name__ == '__main__':
    app.run()