from flask_wtf import FlaskForm
from wtforms import StringField, URLField, SubmitField
from wtforms.validators import InputRequired, Length, URL
from flask_ckeditor import CKEditorField


class PostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[InputRequired(), Length(min=1, max=250, message="Blog Post Title must be between %(min)d and %(max)d characters.")])
    subtitle = StringField("Subtitle", validators=[InputRequired(), Length(min=1, max=250, message="Subtitle must be between %(min)d and %(max)d characters.")])
    author = StringField("Your Name", validators=[InputRequired(), Length(min=1, max=250, message="Your Name must be between %(min)d and %(max)d characters.")])
    img_url = URLField("Blog Image URL", validators=[InputRequired(), URL(), Length(min=1, max=250, message="The Blog Image URL must be between %(min)d and %(max)d characters.")])
    body = CKEditorField("Blog Content", validators=[InputRequired()])
    submit = SubmitField("SUBMIT POST")
