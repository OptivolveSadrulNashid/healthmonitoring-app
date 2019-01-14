from flask_wtf import Form, RecaptchaField
from wtforms import StringField, PasswordField, DateTimeField, SelectField, TextAreaField
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email, Length, EqualTo)
from wtforms.fields.html5 import DateField
from wtforms_components import TimeField
from flask import Markup
from wtforms import Form, RadioField, FloatField, IntegerField, FileField, validators

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Email(message='Please input valid email')])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    
class LoginForm(Form):
    recap = RecaptchaField()
    
# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#Bmi form
class BMIForm(Form):
    weight = FloatField('Weight in kg', [validators.DataRequired(message='Please input your weight')])
    height = FloatField('Height in meter', [validators.DataRequired(message='Please input your height')])

#calorie form 
class CalorieForm(Form):
    gender= RadioField('Choose Gender', choices=[('male','Male'),('female','Female')])
    age= FloatField('Age in years', [validators.DataRequired(message='Please input your age')])
    height= FloatField('Height in centimeter', [validators.DataRequired(message='Please input your height')])
    weight= FloatField('Weight in kg', [validators.DataRequired(message='Please input your weight')])
    excercise= SelectField('Exercise level', choices=[('', 'Select'), ('1.2','sedentary people'), ('1.3', 'moderately active'), ('1.4','active people')], default='Select')

#feedback form
class FeedbackForm(Form):
    name = StringField('Full Name', [validators.Length(min=1, max=50)])
    email = StringField('Email Address', [validators.Email(message='Please input valid email')])
    feedback = TextAreaField('Feedback', [validators.Length(min=10)])

#profile form
class ProfileForm(Form):
    phone_no = IntegerField('Phone no.:', [validators.DataRequired(message='please input phone no')])
    address = TextAreaField('Address:', [validators.Length(min=10)])
    blood_group = StringField('Blood Group:', [validators.Length(min=2, max=20)])
    allergies = TextAreaField('If any allergies:', [validators.optional()])
    heartrate = StringField('Heart rate:', [validators.DataRequired(message='please input your latest heart-rate!')])
    pressure = StringField('Blood Pressure:', [validators.DataRequired(message='please input your latest blood pressure!')])


#ehr form
class EHRForm(Form):
    topic = StringField('Topic', [validators.Length(min=3, max=50)])
    description= TextAreaField('Health Record', [validators.Length(min=30)])
    #myfile = FileField('upload any file if any' )

#macro form
class MacroForm(Form):
    calorie= FloatField('Calories per day', [validators.DataRequired(message='Please input your require calorie')])
    ratio= SelectField('Set your goal', choices=[('s', 'Select'), ('m','moderate'), ('z', 'zone diet'), ('lf','low fat')], default='Select')
    meals= RadioField('Meals per day', choices=[('3','Three'),('4','Four'),('5','Five')])

#routine form
class TaskForm(Form):
	title = StringField('title', validators=[DataRequired()])
	content = TextAreaField('content')
	priority = SelectField('priority', choices=[('', 'Priority'), ('low','low'), ('medium', 'medium'), ('high','high')], default='Priority')
	date = DateField('Pick a Date', validators=[DataRequired()])
	date_time = TimeField('pick a time', validators=[DataRequired()])    
