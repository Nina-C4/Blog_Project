# --------------------------------------------------------------------
# Project Name: Blog Project
# Description:
#       Fully functional blog built with Python Flask, Bootstrap and PostgreSQL.
# ----------------------------------------------------------------------------- #

import datetime as dt
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from forms import NewPostForm, RegisterForm, LoginForm, CommentForm
import json
import os
from dotenv import load_dotenv
import smtplib


load_dotenv()
MY_EMAIL = os.environ['EMAIL']
PASS = os.environ['PASS']
G_URL = "smtp.gmail.com"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_KEY']
ckeditor = CKEditor(app)
Bootstrap5(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# py_deco for create, edit, delete routes
# docu: https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def create_user():
    with app.app_context():
        new_user = User(
            name='Nina',  # type: ignore[call-arg]
            email='admin@email.com',  # type: ignore[call-arg]
            password = generate_password_hash(password='123456', method='pbkdf2:sha256', salt_length=10) # type: ignore[call-arg]
        )
        db.session.add(new_user)
        db.session.commit()

def create_posts_from_json(_filename):
    with app.app_context():
        with open(f"{_filename}.json", "r", encoding="utf-8") as j_file:
            a_list = json.load(j_file)

        for post in a_list:
            user = db.session.query(User).get(post['user_id'])

            new_post = BlogPost(
                author=user,
                title=post['title'],
                subtitle=post['subtitle'],
                date=post['date'],
                body=" ".join(post['body']),
                img_url=post['img_url'],
            )
            db.session.add(new_post)
            db.session.commit()


# ----------------------------------------------------------------- #
# Create database
class Base(DeclarativeBase):
    pass

if os.environ.get("LOCAL") == "True":
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///blog_posts.db")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create tables and configure
# Parent of BlogPost_objs and Comment_objs
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    # ! Relational databases: this acts like a list of BlogPost_objs attached to each User
    posts = relationship(argument="BlogPost", back_populates="author")
    comments = relationship(argument="Comment", back_populates="comment_author")

# ! Relational databases: Create ForeignKey and reference to the User object
# Child of User | Parent of Comment
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(150), nullable=False)
    date: Mapped[str] = mapped_column(String(30), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    author = relationship(argument="User", back_populates="posts")
    comments = relationship(argument="Comment", back_populates="parent_post")

# Create Comments table: one-to-many with both Users and BlogPosts
# Child of both User and BlogPost
class Comment(db.Model):
    __tablename__="comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[str] = mapped_column(String(30),nullable=False)

    comment_author = relationship(argument="User", back_populates="comments")
    parent_post = relationship(argument="BlogPost", back_populates="comments")


# # create all table structures
with app.app_context():
    db.create_all()

# create records in BlogPost.db and User.db
# # comment below lines after the 1st run
# if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#     create_user()
#     create_posts_from_json('blog_data')

# ----------------------------------------------------------------- #

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        user = db.session.execute(db.select(User).where(User.email==email)).scalar()
        if user:
            flash("You've already signed up with this email, please log in.","info")
            return redirect(url_for('login'))

        new_user = User(
            name=form.name.data,  # type: ignore[call-arg]
            email=form.email.data,  # type: ignore[call-arg]
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256',salt_length=10)  # type: ignore[call-arg]
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash(f'Registration successful<br>Welcome, {current_user.name}!<br>You are logged in',"success")
        return redirect(url_for('home'))
    return render_template("register.html",
                           form=form,
                           current_user=current_user,
                           title='Register',
                           subtitle='Start Contributing to the Blog!',
                           bg_image="register-bg.jpg"
                           )


@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        passw = form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash("This email does not exist, please try again or Register","info")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, passw):
            flash('Password incorrect, please try again','error')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash(f"Welcome back, {current_user.name}!<br>You are logged in","success")
            return redirect(url_for('home'))

    return render_template("login.html",
                           form=form,
                           current_user=current_user,
                           title='Log In',
                           subtitle='Welcome back!',
                           bg_image="login-bg.jpg"
                           )


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.','success')
    return redirect(url_for('home'))


@app.route('/')
def home():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html",
                           all_posts=posts,
                           current_user=current_user,
                           title='Blog Project',
                           subtitle='A collection of random musings',
                           bg_image="home-bg.jpg"
                           )


@app.route("/post/<int:post_id>", methods=['GET','POST'])
def show_post(post_id):
    sel_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('We are looking forward to reading your contributions!<br>It only takes 15 seconds to register/login','info')
            return redirect(url_for('register'))

        new_comm = Comment(
            text=comment_form.text.data,
            user_id=current_user.id,
            post_id=sel_post.id,
            date=dt.date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_comm)
        db.session.commit()
        comment_form = CommentForm()

        return redirect(url_for('show_post',post_id=sel_post.id))

    return render_template("post.html",
                           current_user=current_user,
                           post=sel_post,
                           form=comment_form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = NewPostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=dt.date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("write-post.html",
                           form=form,
                           current_user=current_user,
                           title='New Post',
                           subtitle="You're going to make a great blog post!",
                           bg_image="edit-bg.jpg"
                           )


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = NewPostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("write-post.html",
                           form=edit_form,
                           is_edit=True,
                           current_user=current_user,
                           title='Edit Post',
                           subtitle="You're going to make a great blog post!",
                           bg_image="edit-bg.jpg"
                           )


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/about")
def about():
    return render_template("about.html",
                           current_user=current_user,
                           title='About Me',
                           subtitle='This is what I do.',
                           bg_image="about-bg.jpg"
                           )


@app.route("/contact", methods=['GET','POST'])
def contact():
    if request.method == 'GET':
        return render_template("contact.html",
                               current_user=current_user,
                               title='Contact Me',
                               subtitle='Have questions? I have answers.',
                               bg_image="contact-bg.jpg"
                               )

    elif request.method == 'POST':
        user_data = request.form
        print(user_data)        # it returns a list of tuples (html id, value)

        message = (f"Name: {user_data['name']}\n"
                   f"Email: {user_data['email']}\n"
                   f"Phone: {user_data['phone']}\n"
                   f"Message:\n"
                   f" {user_data['message']}")

        with smtplib.SMTP(G_URL,587, timeout=120) as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=PASS)
            connection.sendmail(from_addr=MY_EMAIL, to_addrs="nina.patru.pt@gmail.com",
                                msg=f"Subject: My Blog | New subscriber\n\n"
                                    f"{message}")

        return render_template(
            'contact.html',
            title='Message successfully sent!',
            subtitle = 'Have questions? I have answers.',
            bg_image="contact-bg.jpg"
        )

if __name__ == "__main__":
    app.run(debug=False, host='localhost',port=3333)
