# amaterus_admin_gradio

```shell
poetry run python scripts/main.py --env_file .env
```

```shell
sudo docker build -t amaterus_admin_gradio .
sudo docker run --rm --env-file $PWD/.env -p "127.0.0.1:7860:7860" amaterus_admin_gradio
```

```shell
poetry export --without-hashes -o requirements.txt
poetry export --without-hashes --with dev -o requirements-dev.txt
```