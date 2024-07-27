FROM python:3.12-slim as build

WORKDIR /app

RUN pip install poetry==1.8.3

COPY pyproject.toml poetry.lock ./

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN poetry install --only main --no-root 

FROM python:3.12-slim as runtime

WORKDIR /app

ARG USERNAME=app
ARG UID=1000
ARG GID=$UID

RUN groupadd --gid $GID $USERNAME \
    && useradd --uid $UID --gid $GID $USERNAME

RUN chown -R $USERNAME:$USERNAME /app

USER $USERNAME

COPY --from=build /app/.venv/ ./.venv/
    
COPY ./flask_chat/ .

COPY entrypoint.sh .

COPY db_configurations/scripts/init_db.py .

ENTRYPOINT [ "sh", "./entrypoint.sh" ]
