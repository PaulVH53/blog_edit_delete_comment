from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    content = StringField('Content', validators=[DataRequired(), Length(min=10)], render_kw={'rows': 10})
    submit = SubmitField('Post')
    
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class CommentForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired(), Length(min=2)], render_kw={'rows': 10})
    submit = SubmitField('Submit')
