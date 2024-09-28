<h1 align=center><b>YappSpace</b></h1>
<p align=center>simple private chatroom for multiple users to chat and have fun.<br>
<i><b>*Currently in development stage</b></i></p>

<p align=center><a href="https://github.com/crudenesss/flask-chat/issues">Report Bug/Request Feature</a></p>

## Table of contents

- [Getting started](#getting-started)
    - [Requirements](#requirements)
    - [Deployment guide](#deployment-guide)
- [Description](#description)
    - [Available features](#available-features)
    - [Technology Stack](#technology-stack)
- [Roadmap](#roadmap)

# Getting started

### Requirements
- Docker

### Deployment guide

#### 1. Install source code
Use `git clone` to download this repository with everything necessary.

#### 2. Configure environmental variables

File `env_example` contains all required variables. You may just rename this file to `.env` and replace placeholder values with other preffered.

#### 3. Docker time!

Navigate to project directory in CLI and type this command for running the application (add -d flag if you need your logs hidden):
```
docker compose up [-d]
```

#### 4. Have fun!


# Description

### Available features

**Interactive chat:**
- Supports communication between several users in the chatroom.
- Supports real time messaging using Web-Sockets.
- Each message displays message's author, message itself and timestamp.

**User profile:**
- Contains `username`, `email` as required unique parameters, other optional parameters: `bio`.
- User can edit their own profile info, such as `username`, `email`, `bio`.
- User can upload their own profile picture. Basic image validation is also implemented. Otherwise default profile picture is rendered.
- Users can view each other's profiles.


### Technology Stack

Listing of frameworks, tools and other stuff used in this project.

#### Language: Python
- **Framework:** Flask
- **Package management:** Poetry
- **Web-Sockets:** Flask-SocketIO
- built-in **logging** framework
- **Sessions:** Flask-JWT-Extended
- **Other:** WTForms, argon2
- **ORM:** SQLAlchemy

#### Deployment
- **Orchestration:** Docker compose
- **Application deployment:** Gunicorn

#### Database: PostgreSQL

## Roadmap

Visit [Issues](https://github.com/crudenesss/flask-chat/issues) to get info about the most relevant upcoming features and theirs developing state.

Those and other upcoming tweaks and features to be released listed below:

- [ ] Securing application with HTTPS and WSS
- [ ] Simple application design
- [ ] PGP keys
- [ ] Admin panel and moderation system
- [x] Users profile view
- [ ] Changing password
- [ ] Verification of renewed user information with user password