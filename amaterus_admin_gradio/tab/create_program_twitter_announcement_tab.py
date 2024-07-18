import os
import re
from datetime import datetime
from logging import Logger
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from pydantic import BaseModel

from ..graphql_client import (
    Client,
    CreateProgramTwitterAnnouncement,
    CreateProgramTwitterAnnouncementWithoutImage,
)

JST = ZoneInfo("Asia/Tokyo")


class FetchTwitterTweetOembedApiResponse(BaseModel):
    author_url: str
    author_name: str
    url: str
    html: str


def fetch_twitter_tweet_oembed_data(
    twitter_tweet_url_or_id: str,
) -> FetchTwitterTweetOembedApiResponse:
    twitter_tweet_url_or_id = twitter_tweet_url_or_id.strip()

    remote_tweet_id: str | None = None
    if twitter_tweet_url_or_id.startswith("https://"):
        urlp = urlparse(twitter_tweet_url_or_id)
        if urlp.netloc != "twitter.com":
            raise Exception(f"Invalid URL: {twitter_tweet_url_or_id}")

        remote_tweet_id = os.path.basename(urlp.path)
        if len(remote_tweet_id) == 0:
            raise Exception(f"Invalid URL: {twitter_tweet_url_or_id}")
    else:
        if not re.match(r"^\d+$", twitter_tweet_url_or_id):
            raise Exception(f"Invalid Twitter tweet ID: {twitter_tweet_url_or_id}")

        remote_tweet_id = twitter_tweet_url_or_id

    res = requests.get(
        "https://publish.twitter.com/oembed",
        headers={
            "User-Agent": "Amaterusbot (+https://amaterus.aoirint.com)",
        },
        params={
            "url": f"https://twitter.com/i/status/{remote_tweet_id}",
            "partner": "",
            "hide_thread": "false",
        },
    )
    res.raise_for_status()

    api_response = FetchTwitterTweetOembedApiResponse.model_validate(res.json())
    return api_response


def create_create_program_twitter_announcement_tab(
    graphql_client: Client,
    logger: Logger,
) -> gr.Tab:
    with gr.Tab(label="プログラムにXの投稿を追加") as tab:
        gr.Markdown("# プログラムにXの投稿を追加")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    clear_twitter_tweet_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    twitter_tweet_url_or_id_text_field = gr.Textbox(
                        label="Xの投稿URL または 投稿ID",
                        interactive=True,
                    )
                with gr.Row():
                    fetch_tweet_data_button = gr.Button(
                        value="X から投稿情報を取得",
                    )
                with gr.Row():
                    remote_tweet_id_text_field = gr.Textbox(
                        label="X 上の投稿ID",
                        interactive=False,
                    )
                    tweet_time_text_field = gr.Textbox(
                        label="投稿時間",
                        interactive=False,
                    )
                with gr.Row():
                    twitter_screen_name_text_field = gr.Textbox(
                        label="スクリーンネーム",
                        interactive=False,
                    )
                    twitter_display_name_text_field = gr.Textbox(
                        label="アカウント表示名",
                        interactive=False,
                    )
                with gr.Row():
                    twitter_account_drop = gr.Dropdown(
                        label="X アカウント",
                        interactive=True,
                    )
                with gr.Row():
                    tweet_embed_html_text_field = gr.Textbox(
                        label="埋め込みコード",
                        interactive=False,
                    )

            with gr.Column():
                with gr.Row():
                    clear_twitter_tweet_image_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    twitter_tweet_image_index_text_field = gr.Textbox(
                        label="画像インデックス",
                        interactive=True,
                    )
                with gr.Row():
                    twitter_tweet_image_url_text_field = gr.Textbox(
                        label="画像URL",
                        interactive=True,
                    )

            with gr.Column():
                with gr.Row():
                    clear_project_field_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    project_drop = gr.Dropdown(
                        label="プロジェクト",
                        interactive=True,
                    )
                with gr.Row():
                    program_drop = gr.Dropdown(
                        label="プログラム",
                        interactive=True,
                    )
                with gr.Row():
                    person_drop = gr.Dropdown(
                        label="投稿者",
                        interactive=True,
                    )
                with gr.Row():
                    add_program_twitter_announcement_button = gr.Button(
                        value="X の投稿を追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_program_twitter_announcement_id_text_field = gr.Textbox(
                        label="追加された X の投稿のデータベース上のID",
                        interactive=False,
                    )

        def handle_tab_selected() -> Any:
            initial_data = (
                graphql_client.get_create_program_twitter_announcement_initial_data()
            )
            return [
                gr.Dropdown(
                    choices=list(
                        map(
                            lambda twitter_account: (
                                f"{twitter_account.name} "
                                f"(@{twitter_account.twitter_screen_name})",
                                twitter_account.id,
                            ),
                            initial_data.twitter_account_list,
                        ),
                    ),
                ),
                gr.Dropdown(
                    choices=list(
                        map(
                            lambda project: (project.name, project.id),
                            initial_data.project_list,
                        ),
                    ),
                ),
                gr.Dropdown(
                    choices=list(
                        map(
                            lambda person: (person.name, person.id),
                            initial_data.person_list,
                        ),
                    ),
                ),
            ]

        def handle_project_changed(
            project_id: str,
        ) -> Any:
            if project_id is None or len(project_id) == 0:
                return gr.Dropdown(
                    value=None,
                    choices=None,
                )

            response = graphql_client.get_program_project_list_by_project_id(
                project_id=project_id,
            )
            project = response.project
            if project is None:
                raise Exception("Project must not be None")

            return gr.Dropdown(
                choices=list(
                    map(
                        lambda program_project: (
                            program_project.program.title,
                            program_project.program.id,
                        ),
                        project.program_project_list,
                    ),
                ),
            )

        def handle_fetch_tweet_data_button_clicked(
            twitter_tweet_url_or_id: str | None,
        ) -> Any:
            if twitter_tweet_url_or_id is None or len(twitter_tweet_url_or_id) == 0:
                raise Exception("Invalid Twitter tweet URL or ID")

            twitter_tweet_oembed_response = fetch_twitter_tweet_oembed_data(
                twitter_tweet_url_or_id=twitter_tweet_url_or_id,
            )
            tweet_url = twitter_tweet_oembed_response.url
            remote_tweet_id = os.path.basename(tweet_url)

            snowflake_timestamp = ((int(remote_tweet_id) >> 22) + 1288834974657) / 1000
            snowflake_tweet_time = datetime.fromtimestamp(
                snowflake_timestamp
            ).astimezone(JST)

            author_url = twitter_tweet_oembed_response.author_url
            screen_name = os.path.basename(author_url)

            author_name = twitter_tweet_oembed_response.author_name

            unsafe_html = twitter_tweet_oembed_response.html
            sanitized_html = unsafe_html.strip()

            script_tag_text = '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'  # noqa: B950
            if sanitized_html.endswith(script_tag_text):
                sanitized_html = sanitized_html[: -len(script_tag_text)]

            if "<script" in sanitized_html:
                raise Exception(f"Invalid Twitter tweet embed html: {sanitized_html}")

            sanitized_html = sanitized_html.strip()

            response = graphql_client.get_twitter_account_by_screen_name(
                twitter_screen_name=screen_name,
            )
            twitter_account_list = response.twitter_account_list
            if len(twitter_account_list) == 0:
                raise Exception("The length of Twitter Account List must not be zero")

            twitter_account = twitter_account_list[0]

            return [
                remote_tweet_id,
                snowflake_tweet_time.isoformat(),
                sanitized_html,
                screen_name,
                author_name,
                twitter_account.id,
            ]

        def handle_add_program_twitter_announcement_button_clicked(
            remote_tweet_id: str,
            twitter_account_id: str,
            tweet_time_string: str,
            tweet_embed_html: str,
            twitter_tweet_image_index: str,
            twitter_tweet_image_url: str,
            program_id: str,
            person_id: str,
        ) -> Any:
            tweet_time = datetime.fromisoformat(tweet_time_string)

            response_tweet = graphql_client.create_twitter_tweet(
                remote_tweet_id=remote_tweet_id,
                twitter_account_id=twitter_account_id,
                tweet_time=tweet_time,
                tweet_embed_html=tweet_embed_html,
            )
            if response_tweet.twitter_tweet is None:
                raise Exception("twitter_tweet must not be None")

            twitter_tweet_id = response_tweet.twitter_tweet.id

            twitter_tweet_image_id: str | None = None
            if (
                len(twitter_tweet_image_index) == 0
                and len(twitter_tweet_image_url) == 0
            ):
                response_tweet_image = graphql_client.create_twitter_tweet_image(
                    twitter_tweet_id=twitter_tweet_id,
                    twitter_tweet_image_index=int(twitter_tweet_image_index),
                    twitter_tweet_image_url=twitter_tweet_image_url,
                )
                if response_tweet_image.twitter_tweet_image is None:
                    raise Exception("twitter_tweet_image must not be None")

                twitter_tweet_image_id = response_tweet_image.twitter_tweet_image.id

            response_program_twitter_announcement = (
                graphql_client.create_program_twitter_announcement(
                    program_id=program_id,
                    person_id=person_id,
                    twitter_tweet_id=twitter_tweet_id,
                    twitter_tweet_image_id=twitter_tweet_image_id,
                )
            )

            program_twitter_announcement = (
                response_program_twitter_announcement.program_twitter_announcement
            )
            if program_twitter_announcement is None:
                raise Exception("program_twitter_announcement must not be None")

            return [
                program_twitter_announcement.id,
            ]

        clear_twitter_tweet_field_button.add(
            components=[
                twitter_tweet_url_or_id_text_field,
                remote_tweet_id_text_field,
                tweet_embed_html_text_field,
                tweet_time_text_field,
            ],
        )

        clear_twitter_tweet_image_field_button.add(
            components=[
                twitter_tweet_image_index_text_field,
                twitter_tweet_image_url_text_field,
            ],
        )

        clear_project_field_button.add(
            components=[
                project_drop,
                program_drop,
                person_drop,
            ],
        )

        tab.select(
            fn=handle_tab_selected,
            outputs=[
                twitter_account_drop,
                project_drop,
                person_drop,
            ],
        )

        fetch_tweet_data_button.click(
            fn=handle_fetch_tweet_data_button_clicked,
            inputs=[twitter_tweet_url_or_id_text_field],
            outputs=[
                remote_tweet_id_text_field,
                tweet_time_text_field,
                tweet_embed_html_text_field,
                twitter_screen_name_text_field,
                twitter_display_name_text_field,
                twitter_account_drop,
            ],
        )

        add_program_twitter_announcement_button.click(
            fn=handle_add_program_twitter_announcement_button_clicked,
            inputs=[
                remote_tweet_id_text_field,
                twitter_account_drop,
                tweet_time_text_field,
                tweet_embed_html_text_field,
                twitter_tweet_image_index_text_field,
                twitter_tweet_image_url_text_field,
                program_drop,
                person_drop,
            ],
            outputs=[
                added_program_twitter_announcement_id_text_field,
            ],
        )

        project_drop.select(
            fn=handle_project_changed,
            inputs=project_drop,
            outputs=program_drop,
        )

    return tab
