from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_gravatar import Gravatar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from forms import PostForm, RegisterForm, LoginForm, CommentForm
from flask_ckeditor import CKEditor
from html_sanitizer import Sanitizer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from functools import wraps
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


# Decorator used for admin access
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if the user has not logged return abort with 403 error
        if current_user.is_anonymous:
            return abort(403)
        # if the user is not an admin return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


application = Flask(__name__)
application.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

# Initialize the CKEditor
ckeditor = CKEditor(application)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(application)

# Connect to the database
application.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URI']
db = SQLAlchemy(model_class=Base)
db.init_app(application)

# Provides gravatar images for users.
gravatar = Gravatar(application,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# Configure database Tables

# User Table
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    # One-to-many relationship with the Blog posts.
    posts: Mapped[list["BlogPost"]] = relationship(back_populates="author")

    # One-to-many relationship with the Comments.
    comments: Mapped[list["Comment"]] = relationship(back_populates="comment_author")


# Blogpost Table
class BlogPost(db.Model):
    __tablename__ = 'blogpost'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # Many-to-one relationship with the User.
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped["User"] = relationship(back_populates="posts")

    # One-to-many relationship with the Comments.
    comments: Mapped[list["Comment"]] = relationship(back_populates="parent_post")


# Comments Table
class Comment(db.Model):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Many-to-one relationship with the User.
    comment_author: Mapped["User"] = relationship(back_populates="comments")
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    # Many-to-one relationship with the Blog Posts.
    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")
    post_id: Mapped[int] = mapped_column(ForeignKey("blogpost.id"))


with application.app_context():
    db.create_all()


# Flask-login callback. This callback is used to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@application.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        registered_user = db.session.execute(db.select(User).where(User.email == register_form.email.data)).scalar()
        if registered_user is not None:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        new_user = User(
            email=register_form.email.data,
            password=generate_password_hash(register_form.password.data, method="pbkdf2"),
            name=register_form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=register_form)


# TODO: Retrieve a user from the database based on their email.
@application.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == login_form.email.data)).scalar()

        if user is None:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        if not check_password_hash(user.password, login_form.password.data):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('home'))
    return render_template("login.html", form=login_form)


@application.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@application.route('/')
def home():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@application.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        clean_data = sanitizer.sanitize(comment_form.comment.data)
        new_comment = Comment(
            text=clean_data,
            author_id=current_user.id,
            post_id=requested_post.id
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("post.html", post=requested_post, form=comment_form)


# TODO: Use a decorator so only an admin user can create a new post
@application.route('/make-post', methods=['GET', 'POST'])
@admin_only
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
            author_id=current_user.id,
            date=current_date.strftime("%B %d, %Y"),
            body=clean_data,
            img_url=post_form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=post_form, edit=edit)


# TODO: Use a decorator so only an admin user can edit a post
@application.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    edit = True
    edit_form = PostForm()
    current_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    if edit_form.validate_on_submit():
        current_post.title = edit_form.title.data
        current_post.subtitle = edit_form.subtitle.data
        current_post.body = sanitizer.sanitize(edit_form.body.data)
        current_post.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))

    if (request.method == "GET") and (current_post is not None):
        edit_form.title.data = current_post.title
        edit_form.subtitle.data = current_post.subtitle
        edit_form.body.data = current_post.body
        edit_form.img_url.data = current_post.img_url

    return render_template("make-post.html", form=edit_form, edit=edit, id=post_id)


# TODO: Use a decorator so only an admin user can delete a post
@application.route("/delete/<int:post_id>", methods=["GET"])
@admin_only
def delete_post(post_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))


@application.route("/about")
def about():
    return render_template("about.html")


@application.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    application.run()
