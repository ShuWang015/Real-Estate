import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
import os, base64
import json
import requests
import mash

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string' 


app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'wangshuo'
app.config['MYSQL_DATABASE_DB'] = 'RealBuddy'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


###################################################
#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
conn = mysql.connect()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

def getUsersInfo(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email, address, zipcode FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone() #NOTE return a tuple, (imgdata, pid, caption)

users = getUserList()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

@app.route("/protected", methods=['GET'])
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	user = getUsersInfo(uid)
	msg = 'Hi, ' + flask_login.current_user.id
	return render_template('protected.html', message=msg, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return render_template('login.html', success=True)
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		inpwd = flask.request.form['password']
		if len(inpwd)!=0 and inpwd == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return render_template('login.html', success=False)


@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('home.html', message='Logged out',user=False)

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		address=request.form.get('address')
		zipcode=request.form.get('zipcode')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('registererror'))
	cursor = conn.cursor()
	test =  isInputValid(email,password,address,zipcode)
	if test== "":
		print(cursor.execute("INSERT INTO Users (email, password, address, zipcode) VALUES ('{0}', '{1}', '{2}', '{3}')".format(email, password,address,zipcode)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('home.html', name=email, message='Account Created!', user=user)
	else:
		print("couldn't find all tokens")
		return render_template('registererror.html', message=test,user = False)

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isInputValid(email,password,address,zipcode):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if len(email) == 0:
		return "Please enter email!"
	elif cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return "Email is already in use!"
	if len(password) == 0:
		return "Please enter password!"
	if len(address) == 0:
		return "Please enter address!"
	if len(zipcode) != 5:
		# length of zipcode should be 5
		return "Invalid zipcode!"
	return ""
#end login code
###################################################


###################################################
#default page
@app.route("/", methods=['GET'])
def home():
	return render_template('home.html', message='Welecome to RealBuddy',user = False)
###################################################




###################################################
# begin rental page
@app.route("/rental", methods=['GET','POST'])
@flask_login.login_required
def rental():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	user = getUsersInfo(uid)
	if request.method == 'POST':
		try:
			zipcode=request.form.get('zipcode')
		except:
			print("couldn't find all tokens") 
			return render_template('rental.html',user=user,error='Please enter zip code',base64=base64)
		if len(zipcode)==5:
			avgRent = mash.avg(zipcode)
		else:
			return render_template('rental.html',user=user,error='Zip code is invalid',base64=base64)
		#avgRent = 4000
	
	else:
		zipcode = user[2]
		avgRent = mash.avg(zipcode)
		#avgRent = 3500
	try:
		ls = mash.getNewPropertyList(zipcode, avgRent)
	except:
		return render_template('rental.html',user=user,error='API error! Zip code is invalid',base64=base64)
	return render_template('rental.html',user=user,avgRent=avgRent,zipcode=zipcode,list=ls,base64=base64)

# end rental page
###################################################


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
