# amaterus_admin_gradio

```shell
poetry run python scripts/main.py --env_file .env
```

```shell
sudo docker build -t amaterus_admin_gradio .
sudo docker run --rm --env-file $PWD/.env -p "127.0.0.1:7860:7860" amaterus_admin_gradio
```

```shell
sudo docker build -t docker.aoirint.com/aoirint/amaterus_admin_gradio .
sudo docker push docker.aoirint.com/aoirint/amaterus_admin_gradio
```

```shell
poetry export --without-hashes -o requirements.txt
poetry export --without-hashes --with dev -o requirements-dev.txt
```

## GraphQL Code Generation

- Node 20

```shell
npm install -g graphqurl
```

```shell
gq "https://amaterus-hasura.aoirint.com/v1/graphql" --introspect > schema.graphql
```
