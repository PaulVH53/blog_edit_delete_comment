import os
from jinja2 import Environment, PackageLoader
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Blog, Comment
from forms import BlogForm, LoginForm, CommentForm
from validate_email import validate_email
from datetime import datetime


bcrypt = Bcrypt()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key'

env = Environment(loader=PackageLoader('app', 'templates'))

db.init_app(app)

# create the database tables
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    blogs = Blog.query.order_by(Blog.date_posted.desc()).all()
    return render_template('home.html', blogs=blogs)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists', 'danger')
            form_data = request.form.copy()
            form_data.pop('password')
            form_data.pop('confirm-password')
            return render_template('signup.html', form_data=form_data)

        if not validate_email(email):
            flash('Invalid email address', 'danger')
            email_error = 'Invalid email address'
            return render_template('signup.html', form_data=request.form, email_error=email_error)
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            form_data = request.form.copy()
            form_data.pop('password')
            form_data.pop('confirm-password')
            return render_template('signup.html', form_data=form_data)

        # Generate password hash using bcrypt
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create new User instance with password hash
        new_user = User(email=email, password_hash=password_hash, name=name)

        # Add new user to the database and commit changes
        db.session.add(new_user)
        db.session.commit()
        flash('{}: you have been successfully signed up!'.format(name), 'success')
        return render_template('signup.html', form_data=request.form)

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            user.active = True  # Set active to True when logging in successfully
            db.session.commit()  # Commit the changes to the database
            login_user(user, remember=form.remember.data)
            flash('{}: you have been successfully logged in!'.format(user.name), 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password!', 'error')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    name = current_user.name
    current_user.logout()
    logout_user()
    flash('{}: you have been logged out!'.format(name), 'success')
    return redirect(url_for('login'))


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = BlogForm()
    if form.validate_on_submit():
        new_blog = Blog(title=form.title.data, content=form.content.data, user_id=current_user.id)
        new_blog.date_posted = datetime.now()
        new_blog.date_edited = None
        db.session.add(new_blog)
        db.session.commit()
        flash('{}: your new post has been created!'.format(current_user.name), 'success')
        return redirect(url_for('home'))
    return render_template('create.html', form=form)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    blog = Blog.query.get_or_404(id)

    if blog.user_id != current_user.id:
        return redirect(url_for('home'))

    form = BlogForm()

    if form.validate_on_submit():
        blog.edit(form.title.data, form.content.data)
        db.session.commit()
        flash('Your blog has been updated!', 'success')
        return redirect(url_for('home'))

    elif request.method == 'GET':
        form.title.data = blog.title
        form.content.data = blog.content

    return render_template('edit.html', title='Edit Blog', form=form, legend='Edit Blog', blog=blog)


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    blog = Blog.query.get_or_404(id)
    if request.method == 'POST':
        db.session.delete(blog)
        db.session.commit()
        flash('Your blog has been deleted!', 'success')
        return redirect(url_for('home'))
    return render_template('delete.html', blog=blog)


@app.route('/comment/<int:blog_id>', methods=['GET', 'POST'])
@login_required
def comment(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    form = CommentForm()
    if form.validate_on_submit():
        date_posted = datetime.now()
        content = form.content.data
        author_id = current_user.id
        new_comment = Comment(date_posted=date_posted, content=content, blog_id=blog_id, author_id=author_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
        return redirect(url_for('home'))
    return render_template('comment.html', form=form, blog=blog)


@app.route('/view_comments/<int:blog_id>')
def view(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    comments = Comment.query.filter_by(blog_id=blog_id).order_by(Comment.date_posted.desc())
    return render_template('view_comments.html', blog=blog, comments=comments)


if __name__ == '__main__':
    app.run(debug=True)
