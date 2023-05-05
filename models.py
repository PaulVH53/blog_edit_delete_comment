from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from pytz import timezone
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone('America/Lima')))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)

    def is_active(self):
        return self.active

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def authenticate(email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        else:
            return None

    def logout(self):
        self.active = False
        db.session.commit()


class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone('America/Lima')))
    date_edited = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('blogs', lazy=True, overlaps='user_blogs'),
                             overlaps='user_blogs')
    comments = db.relationship('Comment', backref='blog', lazy=True)

    def __repr__(self):
        return f"Blog('{self.title}', '{self.date_posted}')"

    def edit(self, new_title, new_content):
        self.title = new_title
        self.content = new_content
        self.date_edited = datetime.now(timezone('America/Lima'))

    def __init__(self, title, content, user_id):
        self.title = title
        self.content = content
        self.user_id = user_id
        
    @property
    def comments_count(self):
        return len(self.comments)
        


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone('America/Lima')))
    content = db.Column(db.String(1000), nullable=False)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('comments', lazy=True, overlaps='user_comments'), overlaps='user_comments')

    def __repr__(self):
        return f"Comment('{self.date_posted}', '{self.content}')"
