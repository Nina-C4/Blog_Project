
import datetime as dt
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, func, desc
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from forms import NewPostForm, RegisterForm, LoginForm, CommentForm
import os
from dotenv import load_dotenv
import smtplib
import re


load_dotenv()
APP_EMAIL = os.environ['APP_EMAIL']
PASS = os.environ['PASS']
ADMIN_EMAIL = os.environ['ADMIN_EMAIL']
G_URL = "smtp.gmail.com"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['DEL_CODE'] = os.environ['DELETION_CODE']
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

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def find_phrase(text, query, max_length=250):
    """Finds a phrase containing the query."""
    match = re.search(re.escape(query), text, re.IGNORECASE)
    if match:
        start = match.start()
        sentence_start = max(
            text.rfind(". ", 0, start),
            text.rfind("! ", 0, start),
            text.rfind("? ", 0, start),
            text.rfind("\n", 0, start),
            0  # start of string
        )
        if sentence_start != 0:
            start = sentence_start + 2  # skip delimiter
            if text[start:start + 2].lower() == "p>":
                start += 2  # Skip the "<p>" tag

        end = min(len(text), start + max_length)
        return text[start:end].strip() + "..."

    return text[:max_length].strip() + "..."

def highlight_query(text, query):
    """Highlights the query in the text with orange color."""
    return re.sub(re.escape(query),
                  lambda m: f'<span class="highlighted">{m.group(0)}</span>',
                  text,
                  flags=re.IGNORECASE)

app.jinja_env.filters['highlight_query'] = highlight_query

# ----------------------------------------------------------------- #
# Create database
class Base(DeclarativeBase):
    pass

# Choose DMS: True -> SQLite, False -> PostgreSQL
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


# create all table structures
with app.app_context():
    db.create_all()

# ----------------------------------------------------------------- #

@app.route('/register', methods=['GET','POST'])
def register():
    """Renders the Registration WTForm """
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
    """Renders the Login Form for user authentication."""
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
    # result = db.session.execute(db.select(BlogPost))
    if os.environ.get("LOCAL") == 'False':  # Check for Render.com environment
        # PostgreSQL query
        result = db.session.execute(
            db.select(BlogPost).order_by(desc(func.to_date(BlogPost.date, 'Month DD, YYYY')))
        )
        posts = result.scalars().all()
    else:
        # SQLite query
        result = db.session.execute(
            db.select(BlogPost).order_by(func.strftime('%Y-%m-%d', func.replace(BlogPost.date, ',', '')).desc())
        )
        posts = result.scalars().all()
    visible_posts = posts[:3]  # Initial 3 posts
    all_posts_dicts = [
        {
            'id': post.id,
            'title': post.title,
            'subtitle': post.subtitle,
            'author': {'name': post.author.name},  # Ensure author is a dictionary
            'date': post.date
        }
        for post in posts
    ]
    user_id = -1
    if current_user.is_authenticated:
        user_id = current_user.id

    return render_template("index.html",
                           all_posts=all_posts_dicts,
                           visible_posts=visible_posts,
                           current_user=current_user,
                           user_id=user_id,
                           title='Blog Project',
                           subtitle='A collection of random musings',
                           bg_image="home-bg.jpg"
                           )


@app.route('/search')
def search():
    query = request.args.get('query')  # Get the search query from the URL
    results = []
    if query:
        posts = BlogPost.query.all()

        for post in posts:
            if re.search(re.escape(query), post.title, re.IGNORECASE):
                results.append((post, highlight_query(post.title, query), None))
            elif post.subtitle and re.search(re.escape(query), post.subtitle, re.IGNORECASE):
                results.append((post, highlight_query(f"{post.subtitle}", query), None))
            elif re.search(re.escape(query), post.body, re.IGNORECASE):
                body_phrase = find_phrase(post.body, query)
                results.append((post, highlight_query(f"{body_phrase}", query), None))

            for comment in post.comments:
                if re.search(re.escape(query), comment.text, re.IGNORECASE):
                    comment_phrase = find_phrase(comment.text, query)
                    results.append((post, highlight_query(f"{comment_phrase}", query), comment))

    else:
        results = []

    return render_template('search_results.html',
                           results=results,
                           query=query,
                           current_user=current_user,
                           title='Blog Project',
                           subtitle='A collection of random musings',
                           bg_image="home-bg.jpg"
                           )


@app.route("/post/<int:post_id>", methods=['GET','POST'])
def show_post(post_id):
    sel_post = db.get_or_404(BlogPost, post_id)
    # pass the posts to js as dictionary
    post_dict = {
        'id': sel_post.id,
        'title': sel_post.title,
        'subtitle': sel_post.subtitle,
        'author': {'name': sel_post.author.name},
        'date': sel_post.date
    }

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

        return redirect(url_for('show_post',post_id=sel_post.id,post_dict=post_dict))

    return render_template("post.html",
                           current_user=current_user,
                           post=sel_post,
                           post_dict=post_dict,
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


@app.route("/delete-post/<int:post_id>", methods=["POST"])
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    del_code = request.form.get("delCode")

    if del_code == app.config['DEL_CODE']:
        try:
            comments_to_delete = Comment.query.filter_by(post_id=post_id).all()
            for comment in comments_to_delete:
                db.session.delete(comment)
            db.session.delete(post_to_delete)
            db.session.commit()
            return redirect(url_for('home'))
        except Exception as e:
            # Handle database errors (log, display message, etc.)
            print(f"Database error: {e}")
            abort(500)  # Internal Server Error
    else:
        abort(403)  # Forbidden (incorrect secret key)


@app.route("/about")
def about():
    return render_template("about.html",
                           current_user=current_user,
                           title='About Me',
                           subtitle='Welcome to the party!',
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
            connection.login(user=APP_EMAIL, password=PASS)
            connection.sendmail(from_addr=APP_EMAIL, to_addrs=ADMIN_EMAIL,
                                msg=f"Subject: My Blog | New subscriber\n\n"
                                    f"{message}")

        return render_template(
            'contact.html',
            title='Message successfully sent!',
            subtitle = 'Have questions? I have answers.',
            bg_image="contact-bg.jpg"
        )

if __name__ == "__main__":
    app.run(debug=True, host='localhost',port=5000)
