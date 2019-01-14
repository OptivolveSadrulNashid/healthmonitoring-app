from flask import Flask, render_template, flash, redirect, url_for, session, request, send_file, logging, jsonify
#from data import Articles
from flask_mysqldb import MySQL
from flask_recaptcha import ReCaptcha
from flask_mail import Mail, Message
from werkzeug.datastructures import CombinedMultiDict
from passlib.hash import sha256_crypt
from functools import wraps
from io import BytesIO
import forms
import requests, json

from config import email, password

app = Flask(__name__)
recaptcha = ReCaptcha(app=app)


# Config MySQL, recaptcha, mail
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['RECAPTCHA_PUBLIC_KEY'] ='6LdG82YUAAAAAC1fDjyVyKcQxtkUqSp5okJZS4N0'
app.config['RECAPTCHA_PRIVATE_KEY']= '6LdG82YUAAAAAN6rqMyYYMKbgpePGX5T9AybOHYh'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] =465
app.config['MAIL_USE_SSL'] =True
app.config['MAIL_USERNAME'] =email
app.config['MAIL_PASSWORD'] =password
app.config['MAIL_USE_TLS'] =False

# init MYSQL, mail
mail=Mail(app)
mysql = MySQL(app)


# Index
@app.route('/')
def index():
    return render_template('home.html')


# About & feedback provide unit test
@app.route('/about', methods=['GET', 'POST'])
def feedback():
    form = forms.FeedbackForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        feedback = form.feedback.data
        msg = Message("Feedback from webapp",
                    sender="nashid4722@gmail.com",
                    recipients=["dristysadrul@gmail.com"])
        msg.body = """
        From: %s <%s>
        %s
        """ % (name, email, feedback)
        mail.send(msg)
        flash('Thank you for your feedback', 'success')
        return render_template('about.html', form=form)
        
    return render_template('about.html', form=form)


# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# User Register unit test
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login unit test
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        captcha_response = request.form['g-recaptcha-response']
        if is_human(captcha_response):
            # Create cursor
            cur = mysql.connection.cursor()

            # Get user by username
            result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

            if result > 0:
                # Get stored hash
                data = cur.fetchone()
                password = data['password']

                # Compare Passwords
                if sha256_crypt.verify(password_candidate, password):
                    # Passed
                    session['logged_in'] = True
                    session['username'] = username

                    flash('You are now logged in', 'success')
                    ##need to return here the user profile##
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid login'
                    return render_template('login.html', error=error)
                # Close connection
                cur.close()
            else:
                error = 'Username not found'
                return render_template('login.html', error=error)
        else:
            error = 'Do recaptcha again'
            return render_template('login.html', error=error)

    return render_template('login.html')


#verify recapticha
def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    secret = "6LdG82YUAAAAAN6rqMyYYMKbgpePGX5T9AybOHYh"
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    return response_text['success']


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


#BMI calculator unit test
@app.route('/bmi_calculator', methods=['GET', 'POST'])
@is_logged_in
def bmi():
    form = forms.BMIForm(request.form)
    if request.method == 'POST' and form.validate():
        wet = float(form.weight.data)
        hit = float(form.height.data)
        #calculate bmi 
        calculate = float(wet/hit**(2))

        #make as string
        value = str(round(calculate,2))

        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("INSERT INTO bmical(weight, bmi, people) VALUES(%s, %s, %s)", (wet, calculate, session['username'] ))

        # Commit to DB
        mysql.connection.commit()
        cur.close()
        flash('your bmi is '+value , 'success')
        return render_template('bmi_cal.html', form=form, bmi=value)
    return render_template('bmi_cal.html', form=form)


#calorie calculator
@app.route('/calorie_calculator', methods=['GET', 'POST'])
@is_logged_in
def calorie():
    form = forms.CalorieForm(request.form)
    if request.method == 'POST' and form.validate():
        age= float(form.age.data)
        height = float(form.height.data)
        weight = float(form.weight.data)
        excer = float(form.excercise.data)
        #for males= 10 x (Weight in kg) + 6.25 x (Height in cm) - 5 x age + 5.
        #for females = 10 x (Weight in kg) + 6.25 x (Height in cm) - 5 x age - 161;
        if form.gender.data == 'male':
            result = ((10*weight)+ (6.25*height)-(5*age)+5)*excer
            result2 = result-270
            result3 = result+300
        elif form.gender.data == 'female':
            result = ((10*weight)+ (6.25*height)-(5*age)-161)*excer
            result2 = result-300
            result3 = result+280
        else:
            flash('select your gender' , 'danger')   
        ss= str(round(result,2)) #maintain
        lose = str(round(result2,2)) #lose 
        gain = str(round(result3,2)) #gain
        flash('If you want to gain weight by 10%, you need '+gain +' cal. ' , 'warning')
        flash('you need to maintain '+ss +' cal' , 'success')
        flash('If you want to lose weight by 10%, you need '+lose +' cal. ' , 'warning')
        return render_template('calorie_cal.html', form=form, calculation=ss)

    return render_template('calorie_cal.html', form=form)


#EHR 
#can upload file and description
@app.route('/healthrecord', methods=['GET', 'POST'])
@is_logged_in
def upload():
    form = forms.EHRForm(CombinedMultiDict((request.files, request.form)))       
    if request.method == 'POST' and form.validate():
        topic = form.topic.data
        description = form.description.data 
        file = request.files['inputFile']

        name = file.filename 
        data = file.read()

        cur = mysql.connection.cursor()
        
        cur.execute("INSERT INTO ehr(name, topic, description, filename, filedata) VALUES(%s, %s, %s, %s, %s)", (session['username'], topic, description, name, data))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('health record created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('ehr.html',form = form)


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get patient
    username = session['username']
    result = cur.execute("SELECT * FROM patients WHERE people = %s", [username])
    #get patients data
    patients = cur.fetchall()

    #get ehr 
    cur.execute("SELECT * FROM ehr WHERE name = %s", [username])
    # have all the ehr of particular patients
    ehrs = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', patients=patients, ehrs= ehrs)
    else:
        msg = 'Profile not created yet!'
        return render_template('dashboard.html', msg=msg, r=result, ehrs= ehrs)
    # Close connection
    cur.close()


#file view here
@app.route('/download/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def download(id):
    #get the file 
    cur = mysql.connection.cursor()
    cur.execute("SELECT filedata FROM ehr WHERE id = %s", [id])
    file_data = cur.fetchone()
    # extract from dictionary
    file_data = file_data['filedata']
    cur.close()
    return send_file(BytesIO(file_data))


#go for demostrate data
@app.route('/populate')
def populate():
    # Get data from database
    # Create cursor
    # Create cursor
    cur = mysql.connection.cursor()

    username = session['username']

    cur.execute("SELECT weight FROM bmical WHERE people = %s", [username])
    data = cur.fetchall()
    #get all data in list 
    all_weight= []
    for diction in data:
        Weight = diction['weight']
        all_weight.append(Weight)


    # Commit to DB
    mysql.connection.commit()
    # Close connection
    cur.close()
    # show the graph here
    return render_template('populate.html')


#to jsonify data to view in graphs
@app.route('/data')
@is_logged_in
def data():
    # Create cursor
    cur = mysql.connection.cursor()

    username = session['username']

    cur.execute("SELECT weight FROM bmical WHERE people = %s", [username])
    data = cur.fetchall()
    cur.execute("SELECT date_time FROM bmical WHERE people = %s", [username])
    data2 = cur.fetchall()

    all_weight= []
    all_time = []
    for diction in data:

        Weight = diction['weight']
        all_weight.append(Weight)
        
    for diction in data2:

        Time = diction['date_time']
        all_time.append(Time) 

    # Commit to DB
    mysql.connection.commit()
    # Close connection
    cur.close()
    return jsonify({'results' :all_weight,'resultss':all_time})

#add deatails of patients
@app.route('/patients', methods=['GET', 'POST'])
@is_logged_in
def profile():
    form = forms.ProfileForm(request.form)
    if request.method == 'POST' and form.validate():
        phone = form.phone_no.data
        address= form.address.data
        blood=form.blood_group.data
        heart=form.heartrate.data
        pressure=form.pressure.data
        algs =form.allergies.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO patients(phoneno, address, blood, heartrate, pressure, allergic, people) VALUES(%s, %s, %s, %s, %s, %s, %s)", (phone, address, blood, heart, pressure, algs, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You have successfully completed your profile', 'success')
        return render_template('dashboard.html')
        
    return render_template('addprofile.html',form = form)


# Edit patients details
@app.route('/editprofile/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def editprofile(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get profile by id
    cur.execute("SELECT * FROM patients WHERE id = %s", [id])

    patient = cur.fetchone()
    cur.close()
    # Get form
    form = forms.ProfileForm(request.form)

    # Populate patient form fields
    form.phone_no.data = patient['phoneno']
    form.address.data = patient['address']
    form.blood_group.data =patient['blood']
    form.heartrate.data=patient['heartrate']
    form.pressure.data=patient['pressure']
    form.allergies.data=patient['allergic']

    if request.method == 'POST' and form.validate():
        phone = request.form['phone_no']
        address= request.form['address']
        blood= request.form['blood_group']
        heart= request.form['heartrate']
        pressure= request.form['pressure']
        algs = request.form['allergies']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(phone)
        # Execute
        cur.execute ("UPDATE patients SET phoneno=%s, address=%s , blood=%s, heartrate=%s, pressure=%s, allergic=%s, people=%s WHERE id=%s",(phone, address, blood, heart, pressure, algs, session['username'], id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('profile Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('editprofile.html', form=form)


# balance diet chart
@app.route('/balance_diet', methods=['GET', 'POST'])
@is_logged_in
def dietchart():
    form = forms.MacroForm(request.form)
    if request.method == 'POST' and form.validate():
        calorie = float(form.calorie.data)
        meals = float(form.meals.data)
        # calorie per day
        if form.ratio.data == 's':
            flash('select your ratio' , 'danger')
        elif form.ratio.data == 'm':
            carbs = round(.50*calorie,2)
            protien = round(.25*calorie,2)
            fat= round(.25*calorie,2)
        elif form.ratio.data == 'z':
            carbs = round(.40*calorie,2)
            protien = round(.40*calorie,2)
            fat= round(.20*calorie,2)
        elif form.ratio.data == 'lf':
            carbs = round(.60*calorie,2)
            protien = round(.25*calorie,2)
            fat= round(.15*calorie,2)
        else:
            flash('select your ratio' , 'danger') 
            #diet chart in gram per day-- carbs,protien = 1g 4 cal fat = 1g 9 cal
        gcarbs= round(carbs/4, 2)
        gpro= round(protien/4, 2)
        gfat = round(fat/9, 2)
        # diet in gram per meals
        mcarbs = round(gcarbs/meals, 2)
        mpro = round(gpro/meals, 2)
        mfat = round(gfat/meals, 2)
        return render_template('dietchart.html', form=form, c=carbs,p=protien,f=fat,gc=gcarbs,gp=gpro,gf=gfat,mc=mcarbs,mp=mpro,mf=mfat)
    return render_template('dietchart.html', form=form)


#sample diet for men and women
@app.route('/sample_diet')
def sample_diet():

    return render_template('sample.html')

####################################
####################################

#myroutnine index
@app.route('/my_routine')
def myroutnine():
    return render_template('myroutine.html')

#myroutine home
@app.route('/<string:user_id>/home')
@is_logged_in
def mainr(user_id):
	#todo = models.Todo.select().where(models.Todo.userid == user_id)
        cur = mysql.connection.cursor()

        #username = session['username']

        cur.execute("SELECT * FROM todo WHERE people = %s", [user_id])
        todo = cur.fetchall()
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        return render_template('rountinehome.html', todo=todo)


#add new task
@app.route('/<string:user_id>/new_task', methods=('GET', 'POST'))
@is_logged_in
def newTask(user_id):
    form = forms.TaskForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data,
        content = form.content.data,
        priority = form.priority.data,
        date = form.date.data,
        date_time = form.date_time.data,
        userid = user_id,
        is_done = False	

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO todo(title, content, priority, date, date_time, people, is_done) VALUES(%s, %s, %s, %s, %s, %s, %s)", (title, content, priority, date, date_time, userid, is_done))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()
        return redirect(url_for('mainr', user_id=user_id))	
    return render_template('new_task.html', form=form)


#delete task daily routine
@app.route('/<string:user_id>/<string:task_id>/delete')
@is_logged_in
def del_task(user_id,task_id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM todo WHERE id = %s", [task_id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Task Deleted', 'success')

    return redirect(url_for('mainr', user_id=user_id))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
