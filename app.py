from bs4 import Tag
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text
from forms import PostForm, RegisterForm
from flask_ckeditor import CKEditor
from html_sanitizer import Sanitizer
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os


class Base(DeclarativeBase):
    pass


# edit variable is used to check if the user is editing a post or creating a new post.
edit = False

# Allowed Tags for the html-sanitizer
Tags = {
    "a", "h1", "h2", "h3", "strong", "em", "p", "ul", "ol",
    "li", "br", "sub", "sup", "hr", "img",
}

# Set up the sanitizer to allow the tags specified in the "Tags" variable.
# It also will allow img
# tags as img tags are not allowed by default
sanitizer = Sanitizer({
    "tags": Tags,
    "attributes": {
        "a": ("href", "name", "target", "title", "id", "rel"),
        "img": {"alt", "src"}
    },
    "empty": {"hr", "a", "br", "img"},
})

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

# Initialize the CKEditor
ckeditor = CKEditor(app)

# TODO: Configure Flask-Login

# Connect to the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Configure database Tables
# Blogpost Table
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


# User Table
class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)


# TODO: Create a User table for all your registered users.

with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        new_user = User(
            email=register_form.email.data,
            password=generate_password_hash(register_form.password.data, method="pbkdf2"),
            name=register_form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("register.html", form=register_form)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/logout')
def logout():
    return redirect(url_for('get_all_posts'))


@app.route('/')
def home():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route('/post/<int:post_id>')
def show_post(post_id):
    requested_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    return render_template("post.html", post=requested_post)


# TODO: Use a decorator so only an admin user can create a new post
@app.route('/make-post', methods=['GET', 'POST'])
def add_new_post():
    edit = False
    post_form = PostForm()
    if post_form.validate_on_submit():
        current_date = datetime.datetime.now()
        # Sanitizes the HTML from the body bore storing it in the database.
        clean_data = sanitizer.sanitize(post_form.body.data)
        new_post = BlogPost(
            title=post_form.title.data,
            subtitle=post_form.subtitle.data,
            author=post_form.author.data,
            date=current_date.strftime("%B %d, %Y"),
            body=clean_data,
            img_url=post_form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=post_form, edit=edit)


# TODO: Use a decorator so only an admin user can edit a post
@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    edit = True
    edit_form = PostForm()
    current_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    if edit_form.validate_on_submit():
        current_post.title = edit_form.title.data
        current_post.subtitle = edit_form.subtitle.data
        current_post.author = edit_form.author.data
        current_post.body = sanitizer.sanitize(edit_form.body.data)
        current_post.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))

    if (request.method == "GET") and (current_post is not None):
        edit_form.title.data = current_post.title
        edit_form.subtitle.data = current_post.subtitle
        edit_form.author.data = current_post.author
        edit_form.body.data = current_post.body
        edit_form.img_url.data = current_post.img_url

    return render_template("make-post.html", form=edit_form, edit=edit, id=post_id)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>", methods=["GET"])
def delete_post(post_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run()
