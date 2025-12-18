# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, FloatField, SubmitField, DateField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Email
from flask_wtf.file import FileAllowed
from datetime import datetime


# Form di registrazione
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Length(min=2, max=200)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Conferma Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrati')



# Form di login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Form per il caricamento dell'immagine
class UploadForm(FlaskForm):
    image = FileField('Carica un\'immagine', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Solo immagini!')])
    submit = SubmitField('Carica e Processa')

# Form per Workout
class WorkoutForm(FlaskForm):
    date       = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    name       = StringField(('Name'), validators=[DataRequired(), Length(min=2, max=150)])
    description= TextAreaField(('Description'), validators=[Optional()])
   
# Form per l'aggiornamento dell'esercizio
class UpdateWorkoutForm(WorkoutForm):
    submit     = SubmitField('Update')


# Form per l'aggiornamento dell'esercizio
class AddWorkoutForm(WorkoutForm):
    submit     = SubmitField('Add')


class AddWeeklyWorkoutForm(FlaskForm):
    week_text = TextAreaField(('Weekly Workouts Description'), validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Add Weekly Workouts')

class PerformanceForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    description = TextAreaField(('Description'), validators=[DataRequired(), Length(min=2, max=200)])
    submit = SubmitField('Add Performance')

class EditPerformanceForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    description = TextAreaField(('Description'), validators=[DataRequired(), Length(min=2, max=200)])
    submit = SubmitField('Edit Performance')

class UserStatisticForm(FlaskForm):
    date = DateField(('Date'), validators=[DataRequired()], default=datetime.utcnow)
    exercise = StringField('Exercise', validators=[DataRequired(), Length(min=2, max=150)])
    weight = FloatField('Weight (Kg)', validators=[Optional()])
    reps = IntegerField('Reps', validators=[Optional()])
    submit = SubmitField('Save Stats')


class BulkDeleteStatsForm(FlaskForm):
    submit = SubmitField('Delete Selected')


class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Nuova Password', validators=[Optional()])
    confirm_password = PasswordField('Conferma Password', validators=[Optional(), EqualTo('password')])
    unlock_code = StringField('Unlock Profile', validators=[Optional()])

    submit = SubmitField('Aggiorna Profilo')
