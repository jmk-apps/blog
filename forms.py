from flask_wtf import FlaskForm
from wtforms import StringField, URLField, SubmitField, EmailField, PasswordField
from wtforms.validators import InputRequired, Length, URL, Email
from flask_ckeditor import CKEditorField


# Post form for creating new blog posts.
class PostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[InputRequired(), Length(min=1, max=250,
                                                                               message="Blog Post Title must be between %(min)d and %(max)d characters.")])
    subtitle = StringField("Subtitle", validators=[InputRequired(), Length(min=1, max=250,
                                                                           message="Subtitle must be between %(min)d and %(max)d characters.")])
    img_url = URLField("Blog Image URL", validators=[InputRequired(), URL(), Length(min=1, max=250,
                                                                                    message="The Blog Image URL must be between %(min)d and %(max)d characters.")])
    body = CKEditorField("Blog Content", validators=[InputRequired()])
    submit = SubmitField("SUBMIT POST")


# RegisterForm to register new users.
class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=20,
                                                                             message="Password must be between %(min)d and %(max)d characters.")])
    name = StringField("Name", validators=[InputRequired(), Length(min=1, max=250,
                                                                   message="Name must be between %(min)d and %(max)d characters.")])
    submit = SubmitField("SIGN ME UP!")


# LoginForm to log in existing users.
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("LET ME IN!")


# CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[InputRequired()])
    submit = SubmitField("SUBMIT COMMENT")
