# amaterus_admin_gradio

```shell
poetry run python -m amaterus_admin_gradio --env_file .env
```

```shell
sudo docker build -t amaterus_admin_gradio .
sudo docker run --rm --env-file $PWD/.env -p "127.0.0.1:7860:7860" amaterus_admin_gradio
```

```shell
sudo docker build -t docker.aoirint.com/aoirint/amaterus_admin_gradio .
sudo docker push docker.aoirint.com/aoirint/amaterus_admin_gradio
```

## GraphQL Code Generation

- Node 20
- [graphqurl](https://github.com/hasura/graphqurl) 1.0

```shell
npm install -g graphqurl
```

```shell
poetry run python dev_scripts/fetch_hasura_graphql_schema.py
```

```shell
poetry run ariadne-codegen
```
