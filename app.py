from flask import Flask, render_template,redirect,url_for,request, request, jsonify, make_response, session, flash
import pymysql
import os
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import ps
import jwt
from datetime import datetime, timedelta
from functools import wraps



app = Flask(__name__)

app.config['SECRET_KEY'] = 'idC2f1vGLxZUzEEIlSj_e3FfyFY1xIpvejkOEM3b' #Key to encode cookies data

addressimg = join(dirname(realpath(__file__)), 'static/uploads/images')
app.config['addressimg'] = addressimg

addresspdf = join(dirname(realpath(__file__)), 'static/uploads/pdfs')
app.config['addresspdf'] = addresspdf


# profadd="../static/uploads/images/"+Name+"."+"jpg"
# certadd="../static/uploads/pdfs/"+Name+"."+"pdf"


#Function to query dashboard data from database
def getDashData(loginid):
    connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
    cursor = connection.cursor()
    cursor.execute("select * from rfiduserdata where Email=%s",(loginid))
    data = cursor.fetchall()
    Name=data[0][1]
    cursor.execute("select EntryCount,ExitCount,latest_temp from inoutcount where Email=%s",(loginid))
    data2 = cursor.fetchall()
    cursor.execute("select SR_NO,Date,Time,Inout_Status,temp from userinout where Email=%s",(loginid))
    data3 = cursor.fetchall()
    cursor.execute("select Name,Sname from rfiduserdata where flat_no=%s",(data[0][6]))
    data4 = cursor.fetchall()
    profadd="../static/uploads/images/"+Name+"."+"jpg"
    certadd="../static/uploads/pdfs/"+Name+"."+"pdf"

    dashdata={
        'fullname':data4,
        'email':data[0][4],
        'phone':data[0][5],
        'flatno':data[0][6],
        'regdate':data[0][7],
        'DOB':data[0][8],
        'vaccStatus':data[0][10],
        'flineworker':data[0][11],
        'incount':data2[0][0],
        'outcount':data2[0][1],
        'temp':data2[0][2],
        'value': data3,
        'profileaddress':profadd,
        'certaddress':certadd
    }
    return dashdata


# Function to verify user using user token
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.cookies.get('sites')
        if not token:
            return render_template('index.html', **{'LOGIN':'LOGIN'})
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            print(data.get('user'))
        except:
            return render_template('index.html', **{'LOGIN':'LOGIN'})
        return func(data,*args, **kwargs)
    return decorated


@app.route('/')
def index():
    return render_template('index.html',**{'LOGIN':'LOGIN'})


@app.route('/home')
@token_required
def home(data):
    if data.get('user')=='Admin':
        return render_template('index.html',**{'LOGIN':'ADMIN'})
    print(data)
    connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
    cursor = connection.cursor()
    cursor.execute("select Name from rfiduserdata where Email=%s",(data.get('user')))
    name = cursor.fetchall()
    print(name[0][0])
    return render_template('index.html',**{'LOGIN':name[0][0]})


@app.route('/Dashboard')
@token_required
def dashboard(data):
    if data.get('user')=='Admin':
        return redirect(url_for('sendmembers'))
    dashdata = getDashData(data.get('user'))
    return render_template('userDashboard.html',**dashdata)

# @app.route('/userinfo',methods=['GET','POST'])
# @token_required
# def getuserInfo(data):
#     if request.method=='POST':
#         data = request.form
#         name = data['email']
#         flat = data['flat']
#         connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
#         cursor = connection.cursor()
#         cursor.execute("select Email from rfiduserdata where email=%s and flat_no=%s",(name,flat))
#         loginid=cursor.fetchall()
#         if len(loginid)<1:
#             return render_template('adminDashboard.html')
#         print(loginid)
#         cursor.execute("select SR_NO,Date,Time,Inout_Status,temp from userinout where Email=%s",(loginid))
#         data3 = cursor.fetchall()
#         return render_template('adminDashboard.html',**{'value':data3,'name':name,'flat':flat})
#     return render_template('adminDashboard.html')


@app.route('/userinfo',methods=['GET','POST'])
@token_required
def getuserInfo(data):
    if request.method=='POST':
        data = request.form
        email = data['email']
        dashdata = getDashData(email)
        return render_template('memberinfo.html',**dashdata)

@app.route('/vaccStatus',methods=['GET','POST'])
@token_required
def vaccStatus(data):
    if request.method=='POST':
        formdata = request.form
        status = formdata['approve']
        Email = formdata['Email']
        print(Email)
        print(status)
        if status == "yes":
            connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
            cursor = connection.cursor()
            cursor.execute("select Name from rfiduserdata where Email=%s",Email)
            Name = cursor.fetchall()
            cursor.execute("update rfiduserdata set vacCertify=%s where Email=%s",("Approved",Email))
            connection.commit()
            file = "static/uploads/pdfs/"+Name[0][0]+"toapprove.pdf"
            newname = "static/uploads/pdfs/"+Name[0][0]+".pdf"
            os.rename(file,newname)
        return redirect(url_for('vaccination')) #here


# Home and Login Page: The first Route
@app.route('/',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        idpass = request.form
        loginid = idpass['loginid']
        password = idpass['password']
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Email, password from rfiduserdata where Email=%s and password=%s",(loginid,password))
        data = cursor.fetchall()
        if (len(data)==1):
            # Create JWT Token
            token = jwt.encode(
                {
                    'user': loginid,
                    'expiration': str(datetime.utcnow() + timedelta(seconds=60))
                }, app.config['SECRET_KEY'])

            dashdata = getDashData(loginid)
            response = make_response(render_template('userDashboard.html',**dashdata))
            response.set_cookie('sites',token)
            return response
        else:
            connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
            cursor = connection.cursor()
            cursor.execute("select name, pass from admin where name=%s and pass=%s",(loginid,password))
            data = cursor.fetchall()
            if (len(data)==1):
                token = jwt.encode(
                    {
                        'user': loginid,
                        'expiration': str(datetime.utcnow() + timedelta(seconds=60))
                    }, app.config['SECRET_KEY'])
                cursor.execute("select Name,Mname,Sname,Email,flat_no from rfiduserdata order by flat_no")
                member = cursor.fetchall()
                print(member)
                response = make_response(render_template('getMembers.html',**{'members':member}))
                response.set_cookie('sites',token)
                return response
            return redirect(url_for('index'))



@app.route('/profile-submitted', methods=['GET','POST'])
def editprof():
    if request.method =='POST':
        file = request.files['profile']
        token = request.cookies.get('sites')
        if not token:
            return render_template('index.html', **{'LOGIN':'LOGIN'})
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return render_template('index.html', **{'LOGIN':'LOGIN'})
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name from rfiduserdata where Email=%s",(data.get('user')))
        Name = cursor.fetchall()
        dashdata = getDashData(data.get('user'))
        if file:
            file.filename = Name[0][0]+"."+"jpg"
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['addressimg'],filename))
    return render_template('userDashboard.html',**dashdata)

def isthere(filename, search_path):
   for root, dir, files in os.walk(search_path):
       if filename in files:
           return True
       return False

@app.route('/cert-submitted', methods=['GET','POST'])
def editcert():
    if request.method =='POST':
        file = request.files['cert']
        token = request.cookies.get('sites')
        if not token:
            return render_template('index.html', **{'LOGIN':'LOGIN'})
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return render_template('index.html', **{'LOGIN':'LOGIN'})
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name from rfiduserdata where Email=%s",(data.get('user')))
        Name = cursor.fetchall()
        dashdata = getDashData(data.get('user'))
        if file:
            fnam = Name[0][0]+"."+"pdf"
            print(isthere(fnam,app.config['addresspdf']))
            if isthere(fnam,app.config['addresspdf']):
                os.remove(os.path.join(app.config['addresspdf'],fnam))
            file.filename = Name[0][0]+"toapprove"+"."+"pdf"
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['addresspdf'],filename))
            cursor.execute("update rfiduserdata set vacCertify=%s where Email=%s",("not Approved",data.get('user')))
            connection.commit()
    return render_template('userDashboard.html',**dashdata)



#to view all members of society
@app.route('/members')
@token_required
def sendmembers(data):
    if data.get('user')=='Admin':
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name,Mname,Sname,Email,flat_no from rfiduserdata order by flat_no")
        member = cursor.fetchall()
        print(member)
        return render_template('getMembers.html',**{'members':member})

@app.route('/vaccinations')
@token_required
def vaccination(data):
    if data.get('user')=='Admin':
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name,Mname,Sname,Email from rfiduserdata where vacCertify=%s order by flat_no",("not Approved"))
        member = cursor.fetchall()
        print(member)
        print(type(member))
        return render_template('getvacStatus.html',**{'members':member})

@app.route('/inoutRecord')
@token_required
def inoutRecord(data):
    if data.get('user')=='Admin':
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Email,Date,Time,Inout_Status,temp from userinout")
        record = cursor.fetchall()
        return render_template('inoutRecord.html',**{'record':record})

@app.route('/recordByDate',methods=['GET','POST'])
@token_required
def recordbyDate(data):
    if data.get('user')=='Admin':
        if request.method=='POST':
            data = request.form
            date = data['date']
            print(date)
            if (len(date)>0):
                connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
                cursor = connection.cursor()
                cursor.execute("select Email,Date,Time,Inout_Status,temp from userinout where Date = %s",date)
                record = cursor.fetchall()
                return render_template('inoutRecord.html',**{'record':record})
            else:
                return redirect(url_for('inoutRecord'))
        else:
            return redirect(url_for('inoutRecord'))


@app.route('/logout')
def logout():
    response = make_response(render_template('index.html',**{'LOGIN':'LOGIN'}))
    response.delete_cookie('sites')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=3000,debug=True)