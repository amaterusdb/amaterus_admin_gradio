# syntax=docker/dockerfile:1.5
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

ADD ./scripts /code
ADD ./amaterus_admin_gradio /code/amaterus_admin_gradio

CMD [ "gosu", "user", "python", "/code/add_youtube_live.py" ]
