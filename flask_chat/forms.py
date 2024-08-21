"""WTforms used in application"""

from wtforms import Form, StringField, PasswordField, validators, TextAreaField


class RegForm(Form):
    """Form to sign up to the app

    Args:
        Form (class): Form base class
    """
    username = StringField(
        "Username",
        [
            validators.DataRequired(),
            validators.Length(
                min=5, max=32, message="Username must contain between 5 and 32 symbols"
            ),
        ],
    )
    email = StringField("E-mail", [validators.DataRequired(), validators.Email()])
    password = PasswordField(
        "New Password",
        [
            validators.InputRequired(),
            validators.EqualTo("confirm", message="Passwords must match"),
            validators.Length(
                min=8, max=128, message="Password must contain between 8 and 128 symbols"
            ),
        ],
    )
    confirm = PasswordField("Repeat Password", [validators.InputRequired()])


class LogForm(Form):
    """Form to log in the app"""
    username = StringField("Username", [validators.InputRequired()])
    password = PasswordField("Password", [validators.InputRequired()])


class EditProfileForm(Form):
    """Form to fast-edit info about user"""
    username = StringField(
        "Username",
        [
            validators.DataRequired(),
            validators.Length(
                min=5, max=32, message="Username must contain between 5 and 32 symbols"
            ),
        ],
        render_kw={'class': 'editable', 'readonly': True},
        name="username"
    )
    email = StringField(
        "E-mail",
        [validators.Email()],
        render_kw={'class': 'editable', 'readonly': True},
        name="email"
    )
    bio = TextAreaField(
        "Bio",
        [
            validators.Length(max=256, message="The maximum of 256 symbols are allowed")
        ],
        render_kw={'class': 'editable', 'readonly': True},
        name="bio"
    )

class MessageForm(Form):
    """Form to handle messages within chat"""
    message = TextAreaField(
        [
            validators.Length(max=4096, message="The maximum of 4096 symbols are allowed")
        ],
        name="message"
    )
