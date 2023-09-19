import json
import os
import re
from datetime import datetime
from logging import Logger
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import gradio as gr
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

JST = ZoneInfo("Asia/Tokyo")


class InitialDataResponseProject(BaseModel):
    id: str
    name: str


class InitialDataResponsePerson(BaseModel):
    id: str
    name: str


class InitialDataResponseTwitterAccount(BaseModel):
    id: str
    twitter_screen_name: str
    name: str


class InitialDataResponseData(BaseModel):
    project_list: list[InitialDataResponseProject]
    person_list: list[InitialDataResponsePerson]
    twitter_account_list: list[InitialDataResponseTwitterAccount]


class InitialDataResponse(BaseModel):
    data: InitialDataResponseData


def fetch_initial_data() -> InitialDataResponseData:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        json={
            "query": """
query {
    project_list: projects {
        id
        name
    }

    person_list: persons {
        id
        name
    }

    twitter_account_list: twitter_accounts {
        id
        twitter_screen_name
        name
    }
}
""",
        },
    )
    res.raise_for_status()
    initial_data_response = InitialDataResponse.model_validate(res.json())
    return initial_data_response.data


class ProjectDataResponseProgram(BaseModel):
    id: str
    title: str


class ProjectDataResponseProgramProject(BaseModel):
    program: ProjectDataResponseProgram


class ProjectDataResponseProject(BaseModel):
    program_project_list: list[ProjectDataResponseProgramProject]


class ProjectDataResponseData(BaseModel):
    project: ProjectDataResponseProject


class ProjectDataResponse(BaseModel):
    data: ProjectDataResponseData


def fetch_project_data(
    project_id: str,
) -> ProjectDataResponseProject:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        json={
            "query": """
query A(
    $projectId: uuid!
) {
    project: projects_by_pk(
        id: $projectId
    ) {
        program_project_list: program_projects(
            order_by: {
                program: {
                    start_time: desc
                }
            }
        ) {
            program {
                id
                title
            }
        }
    }
}
""",
            "variables": {
                "projectId": project_id,
            },
        },
    )
    res.raise_for_status()
    project_data_response = ProjectDataResponse.model_validate(res.json())
    return project_data_response.data.project


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


class TwitterAccountDataResponseTwitterAccount(BaseModel):
    id: str


class TwitterAccountDataResponseData(BaseModel):
    twitter_account_list: list[TwitterAccountDataResponseTwitterAccount]


class TwitterAccountDataResponse(BaseModel):
    data: TwitterAccountDataResponseData


def fetch_twitter_account_by_screen_name(
    screen_name: str,
) -> TwitterAccountDataResponseTwitterAccount:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        json={
            "query": """
query A(
    $twitterScreenName: String!
) {
    twitter_account_list: twitter_accounts(
        where: {
            twitter_screen_name: {
                _eq: $twitterScreenName
            }
        }
        order_by: {
            name: asc
        }
        limit: 1
    ) {
        id
    }
}
""",
            "variables": {
                "twitterScreenName": screen_name,
            },
        },
    )
    res.raise_for_status()
    print(res.json())
    twitter_account_data_response = TwitterAccountDataResponse.model_validate(
        res.json()
    )
    return twitter_account_data_response.data.twitter_account_list[0]


class AddProgramTwitterAnnouncementResponseProgramTwitterAnnouncement(BaseModel):
    id: str


class AddProgramTwitterAnnouncementResponseData(BaseModel):
    program_twitter_announcement: AddProgramTwitterAnnouncementResponseProgramTwitterAnnouncement  # noqa: B950


class AddProgramTwitterAnnouncementResponse(BaseModel):
    data: AddProgramTwitterAnnouncementResponseData


def add_program_twitter_announcement(
    program_id: str,
    person_id: str,
    remote_tweet_id: str,
    twitter_account_id: str,
    tweet_time: datetime,
    tweet_embed_html: str,
    twitter_tweet_image_index: int,
    twitter_tweet_image_url: str,
    hasura_admin_secret: str,
) -> AddProgramTwitterAnnouncementResponseProgramTwitterAnnouncement:
    res = requests.post(
        "https://amaterus-hasura.aoirint.com/v1/graphql",
        headers={
            "X-Hasura-Admin-Secret": hasura_admin_secret,
        },
        json={
            "query": """
mutation A(
    $programId: uuid!
    $personId: uuid!
    $remoteTweetId: String!
    $twitterAccountId: uuid!
    $tweetTime: timestamptz!
    $tweetEmbedHtml: String!
    $twitterTweetImageIndex: Int!
    $twitterTweetImageUrl: String!
) {
    program_twitter_announcement: insert_program_twitter_announcements_one(
        object: {
            program_id: $programId
            person_id: $personId
            twitter_tweet: {
                data: {
                    remote_tweet_id: $remoteTweetId
                    tweet_time: $tweetTime
                    tweet_embed_html: $tweetEmbedHtml
                    twitter_account_id: $twitterAccountId
                    twitter_tweet_images: {
                        data: {
                            index: $twitterTweetImageIndex
                            url: $twitterTweetImageUrl
                        }
                        on_conflict: {
                            constraint: twitter_tweet_images_tweet_id_index_key
                            update_columns: [
                                index
                                url
                            ]
                        }
                    }
                }
                on_conflict: {
                    constraint: twitter_tweets_remote_tweet_id_key
                    update_columns: [
                        tweet_time
                        tweet_embed_html
                    ]
                }
            }
        }
    ) {
        id
    }
}
""".strip(),
            "variables": {
                "programId": program_id,
                "personId": person_id,
                "remoteTweetId": remote_tweet_id,
                "twitterAccountId": twitter_account_id,
                "tweetTime": tweet_time.isoformat(),
                "tweetEmbedHtml": tweet_embed_html,
                "twitterTweetImageIndex": twitter_tweet_image_index,
                "twitterTweetImageUrl": twitter_tweet_image_url,
            },
        },
    )
    print(res.json())
    res.raise_for_status()
    add_program_twitter_tweet_response = (
        AddProgramTwitterAnnouncementResponse.model_validate(res.json())
    )
    return add_program_twitter_tweet_response.data.program_twitter_announcement


def create_add_program_twitter_announcement_tab(
    hasura_admin_secret: str,
    logger: Logger,
) -> gr.Tab:
    initial_data = fetch_initial_data()

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
                        choices=list(
                            map(
                                lambda twitter_account: (
                                    f"{twitter_account.name} (@{twitter_account.twitter_screen_name})",
                                    twitter_account.id,
                                ),
                                initial_data.twitter_account_list,
                            ),
                        ),
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
                        choices=list(
                            map(
                                lambda project: (project.name, project.id),
                                initial_data.project_list,
                            ),
                        ),
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
                        choices=list(
                            map(
                                lambda person: (person.name, person.id),
                                initial_data.person_list,
                            ),
                        ),
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

        def handle_project_changed(
            project_id: str,
        ) -> Any:
            if project_id is None or len(project_id) == 0:
                return gr.Dropdown.update(
                    value=None,
                    choices=None,
                )

            project = fetch_project_data(
                project_id=project_id,
            )

            return gr.Dropdown.update(
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

            twitter_account = fetch_twitter_account_by_screen_name(
                screen_name=screen_name,
            )

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

            program_twitter_announcement = add_program_twitter_announcement(
                program_id=program_id,
                person_id=person_id,
                remote_tweet_id=remote_tweet_id,
                twitter_account_id=twitter_account_id,
                tweet_time=tweet_time,
                tweet_embed_html=tweet_embed_html,
                twitter_tweet_image_index=int(twitter_tweet_image_index),
                twitter_tweet_image_url=twitter_tweet_image_url,
                hasura_admin_secret=hasura_admin_secret,
            )

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
