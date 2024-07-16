# syntax=docker/dockerfile:1.7
FROM python:3.11

ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/user/.local/bin:${PATH}

RUN <<EOF
    apt-get update

    apt-get install -y \
        gosu

    apt-get clean
    rm -rf /var/lib/apt/lists/*
EOF

RUN <<EOF
    set -eu

    groupadd -o -g 1000 user
    useradd -m -o -u 1000 -g user user
EOF

ADD ./requirements.txt /
RUN <<EOF
    gosu user pip install -r /requirements.txt
EOF

ADD ./pyproject.toml /code/amaterus_admin_gradio/
ADD ./README.md /code/amaterus_admin_gradio/
ADD ./amaterus_admin_gradio /code/amaterus_admin_gradio/amaterus_admin_gradio

RUN <<EOF
    set -eu

    gosu user pip install -e /code/amaterus_admin_gradio
EOF

ENV GRADIO_SERVER_NAME=0.0.0.0

ENTRYPOINT [ "gosu", "user", "python", "-m", "amaterus_admin_gradio" ]
