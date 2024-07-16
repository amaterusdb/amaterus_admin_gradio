# syntax=docker/dockerfile:1.7
FROM python:3.11 AS poetry-export-stage

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHONUNBUFFERED=1

ARG CONTAINER_UID=999
ARG CONTAINER_GID=999
RUN <<EOF
    set -eu

    groupadd --non-unique --gid "${CONTAINER_GID}" user
    useradd --non-unique --uid "${CONTAINER_UID}" --gid "${CONTAINER_GID}" --create-home user
EOF

RUN <<EOF
    set -eu

    mkdir -p /work
    chown -R "${CONTAINER_UID}:${CONTAINER_GID}" /work
EOF

USER user
WORKDIR /work
ARG PATH="/home/user/.local/bin:${PATH}"

RUN <<EOF
    set -eu

    mkdir -p /home/user/.cache/pip
EOF

ARG PIPX_VERSION=1.6.0
RUN --mount=type=cache,uid="${CONTAINER_UID}",gid="${CONTAINER_GID}",target=/home/user/.cache/pip <<EOF
    set -eu

    pip install "pipx==${PIPX_VERSION}"
    mkdir -p /home/user/.cache/pipx
EOF

ARG POETRY_VERSION=1.8.3
RUN --mount=type=cache,uid="${CONTAINER_UID}",gid="${CONTAINER_GID}",target=/home/user/.cache/pipx <<EOF
    set -eu

    pipx install "poetry==${POETRY_VERSION}"
    mkdir -p /home/user/.cache/pypoetry/{cache,artifacts}
EOF

RUN --mount=type=cache,uid="${CONTAINER_UID}",gid="${CONTAINER_GID}",target=/home/user/.cache/pypoetry/cache \
    --mount=type=cache,uid="${CONTAINER_UID}",gid="${CONTAINER_GID}",target=/home/user/.cache/pypoetry/artifacts <<EOF
    set -eu

    poetry self add poetry-plugin-export
EOF

COPY ./pyproject.toml ./poetry.lock /work/
RUN poetry export -o requirements.txt


FROM python:3.11

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/user/.local/bin:${PATH}

RUN <<EOF
    set -eu

    apt-get update

    apt-get install -y \
        gosu

    apt-get clean
    rm -rf /var/lib/apt/lists/*
EOF

ARG CONTAINER_UID=1000
ARG CONTAINER_GID=1000
RUN <<EOF
    set -eu

    groupadd --non-unique --gid "${CONTAINER_GID}" user
    useradd --non-unique --uid "${CONTAINER_UID}" --gid "${CONTAINER_GID}" --create-home user
EOF

RUN <<EOF
    set -eu

    mkdir -p /home/user/.cache
    chown -R "${CONTAINER_UID}:${CONTAINER_GID}" /home/user/.cache
EOF

COPY --from=poetry-export-stage /work/requirements.txt /code/amaterus_admin_gradio/requirements.txt
RUN --mount=type=cache,uid=${CONTAINER_UID},gid=${CONTAINER_GID},target=/home/user/.cache/pip <<EOF
    set -eu

    gosu user pip install -r /code/amaterus_admin_gradio/requirements.txt
EOF

ADD ./pyproject.toml ./README.md /code/amaterus_admin_gradio/
ADD ./amaterus_admin_gradio /code/amaterus_admin_gradio/amaterus_admin_gradio

RUN --mount=type=cache,uid=${CONTAINER_UID},gid=${CONTAINER_GID},target=/home/user/.cache/pip <<EOF
    set -eu

    gosu user pip install --no-deps -e /code/amaterus_admin_gradio
EOF

RUN <<EOF
    set -eu

    mkdir -p /work
    chown -R "${CONTAINER_UID}:${CONTAINER_GID}" /work
EOF

WORKDIR /work

ENV GRADIO_SERVER_NAME=0.0.0.0

ENTRYPOINT [ "gosu", "user", "python", "-m", "amaterus_admin_gradio" ]
