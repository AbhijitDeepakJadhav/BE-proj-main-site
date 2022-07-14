from flask import Flask, render_template,redirect,url_for,request, request, jsonify, make_response, session, flash
import pymysql
import os
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import ps
import jwt
import math



app = Flask(__name__)

app.config['SECRET_KEY'] = 'idC2f1vGLxZUzEEIlSj_e3FfyFY1xIpvejkOEM3b' #Key to encode cookies data

addressimg = join(dirname(realpath(__file__)), 'static/uploads/images')
app.config['addressimg'] = addressimg

addresspdf = join(dirname(realpath(__file__)), 'static/uploads/pdfs')
app.config['addresspdf'] = addresspdf


# profadd="../static/uploads/images/"+Name+"."+"jpg"
# certadd="../static/uploads/pdfs/"+Name+"."+"pdf"

key = "kladfgwnc"

rand="kldfhjksalieindjjideidindsndjneoiewf"
    
def encryptMessage(msg):
    cipher = ""
    k_indx = 0
    msg= msg+rand
    msg_len = float(len(msg))
    msg_lst = list(msg)
    key_lst = sorted(list(key))
    col = len(key)
    row = int(math.ceil(msg_len / col)) 
    fill_null = int((row * col) - msg_len)
    msg_lst.extend('_' * fill_null)
    matrix = [msg_lst[i: i + col] 
              for i in range(0, len(msg_lst), col)]
    for _ in range(col):
        curr_idx = key.index(key_lst[k_indx])
        cipher += ''.join([row[curr_idx] 
                          for row in matrix])
        k_indx += 1
    return cipher


def decryptMessage(cipher):
    msg = ""
    k_indx = 0
    msg_indx = 0
    msg_len = float(len(cipher))
    msg_lst = list(cipher)
    col = len(key)
    row = int(math.ceil(msg_len / col))
    key_lst = sorted(list(key))
    dec_cipher = []
    for _ in range(row):
        dec_cipher += [[None] * col]
    for _ in range(col):
        curr_idx = key.index(key_lst[k_indx])
  
        for j in range(row):
            dec_cipher[j][curr_idx] = msg_lst[msg_indx]
            msg_indx += 1
        k_indx += 1
    try:
        msg = ''.join(sum(dec_cipher, []))
    except TypeError:
        raise TypeError("This program cannot",
                        "handle repeating words.")
    null_count = msg.count('_')
  
    if null_count > 0:
        return msg[: -null_count]
    return msg

#Function to query dashboard data from database
def getDashData(loginid):
    connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
    cursor = connection.cursor()
    cursor.execute("select * from rfiduserdata where Email=%s",(loginid))
    data = cursor.fetchall()
    Name=data[0][1]
    cursor.execute("select EntryCount,ExitCount,latest_temp from inoutcount where Email=%s",(loginid))
    data2 = cursor.fetchall()
    cursor.execute("select SR_NO,Date,Time,Inout_Status,temp,face_mask from userinout where Email=%s",(loginid))
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
# def token_required(func):
#     @wraps(func)
#     def decorated(*args, **kwargs):
#         token = request.cookies.get('sites')
#         print(token)
#         if not token:
#             return render_template('index.html', **{'LOGIN':'LOGIN'})
#         try:
#             data = decrypt_data(token)
#             print(data.get('user'))
#         except:
#             return render_template('index.html', **{'LOGIN':'LOGIN'})
#         return func(data,*args, **kwargs)
#     return decorated
def token_check():
    token = request.cookies.get('sites')
    # print(token)
    print(token)
    if not token:
        return render_template('index.html', **{'LOGIN':'LOGIN'})
    try:
        data = decryptMessage(token)
        # print(data.get('user'))
        # print(data)
        return data[0:-len(rand)]
    except:
        return render_template('index.html', **{'LOGIN':'LOGIN'})


@app.route('/')
def index():
    return render_template('index.html',**{'LOGIN':'LOGIN'})


@app.route('/home')
def home():
    data = token_check()
    print(data)
    print(type(data))
    if data=='Admin':
        return render_template('index.html',**{'LOGIN':'ADMIN'})
    print(data)
    connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
    cursor = connection.cursor()
    cursor.execute("select Name from rfiduserdata where Email=%s",(data))
    name = cursor.fetchall()
    print(name[0][0])
    return render_template('index.html',**{'LOGIN':name[0][0]})


@app.route('/Dashboard')
def dashboard():
    data = token_check()
    if data=='Admin':
        return redirect(url_for('sendmembers'))
    dashdata = getDashData(data)
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
def getuserInfo():
    data = token_check()
    if request.method=='POST':
        data = request.form
        email = data['email']
        dashdata = getDashData(email)
        return render_template('memberinfo.html',**dashdata)

@app.route('/vaccStatus',methods=['GET','POST'])
def vaccStatus():
    data = token_check()
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
            token = encryptMessage(loginid)
            print(type(token))
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
                token = encryptMessage(loginid)
                print(type(token))
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
        data = token_check()
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name from rfiduserdata where Email=%s",(data))
        Name = cursor.fetchall()
        dashdata = getDashData(data)
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
        data = token_check()
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name from rfiduserdata where Email=%s",(data))
        Name = cursor.fetchall()
        print("data in cert: ",data)
        dashdata = getDashData(data)
        if file:
            fnam = Name[0][0]+"."+"pdf"
            print(isthere(fnam,app.config['addresspdf']))
            if isthere(fnam,app.config['addresspdf']):
                os.remove(os.path.join(app.config['addresspdf'],fnam))
            file.filename = Name[0][0]+"toapprove"+"."+"pdf"
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['addresspdf'],filename))
            cursor.execute("update rfiduserdata set vacCertify=%s where Email=%s",("not Approved",data))
            connection.commit()
    return render_template('userDashboard.html',**dashdata)



#to view all members of society
@app.route('/members')
def sendmembers():
    data = token_check()
    if data=='Admin':
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name,Mname,Sname,Email,flat_no from rfiduserdata order by flat_no")
        member = cursor.fetchall()
        print(member)
        return render_template('getMembers.html',**{'members':member})

@app.route('/vaccinations')
def vaccination():
    data = token_check()
    if data=='Admin':
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Name,Mname,Sname,Email from rfiduserdata where vacCertify=%s order by flat_no",("not Approved"))
        member = cursor.fetchall()
        print(member)
        print(type(member))
        return render_template('getvacStatus.html',**{'members':member})

@app.route('/inoutRecord')
def inoutRecord():
    data = token_check()
    if data=='Admin':
        connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
        cursor = connection.cursor()
        cursor.execute("select Email,Date,Time,Inout_Status,temp,face_mask from userinout")
        record = cursor.fetchall()
        return render_template('inoutRecord.html',**{'record':record})

@app.route('/recordByDate',methods=['GET','POST'])
def recordbyDate():
    data = token_check()
    if data=='Admin':
        if request.method=='POST':
            data = request.form
            date = data['date']
            print(date)
            if (len(date)>0):
                connection = pymysql.connect(host=ps.hostname,user=ps.dbusername,password=ps.dbpassword,db=ps.dbname)
                cursor = connection.cursor()
                cursor.execute("select Email,Date,Time,Inout_Status,temp,face_mask from userinout where Date = %s",date)
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
