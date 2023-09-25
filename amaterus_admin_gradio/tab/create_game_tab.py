from logging import Logger
from typing import Any
from zoneinfo import ZoneInfo

import gradio as gr

from ..graphql_client import Client

JST = ZoneInfo("Asia/Tokyo")


def create_create_game_tab(
    graphql_client: Client,
    logger: Logger,
) -> gr.Tab:
    with gr.Tab(label="ゲームを追加") as tab:
        gr.Markdown("# ゲームを追加")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    clear_button = gr.ClearButton(
                        value="以下のフィールドをクリア",
                    )
                with gr.Row():
                    name_text_field = gr.Textbox(
                        label="名前",
                        interactive=True,
                    )
                with gr.Row():
                    steam_url_text_field = gr.Textbox(
                        label="Steam URL",
                        interactive=True,
                    )
                with gr.Row():
                    epic_games_url_text_field = gr.Textbox(
                        label="Epic Games URL",
                        interactive=True,
                    )
                with gr.Row():
                    nintendo_switch_url_text_field = gr.Textbox(
                        label="Nintendo Switch URL",
                        interactive=True,
                    )
                with gr.Row():
                    playstation_url_text_field = gr.Textbox(
                        label="Playstation URL",
                        interactive=True,
                    )
                with gr.Row():
                    google_play_store_url_text_field = gr.Textbox(
                        label="Google Play Store URL",
                        interactive=True,
                    )
                with gr.Row():
                    apple_app_store_url_text_field = gr.Textbox(
                        label="Apple App Store URL",
                        interactive=True,
                    )
                with gr.Row():
                    website_url_text_field = gr.Textbox(
                        label="Website URL",
                        interactive=True,
                    )
                with gr.Row():
                    add_game_button = gr.Button(
                        value="ゲームを追加",
                        variant="primary",
                    )
                with gr.Row():
                    added_game_id_text_field = gr.Textbox(
                        label="追加されたゲームのデータベース上のID",
                        interactive=False,
                    )

        def handle_add_game_button_clicked(
            name: str,
            steam_url: str,
            epic_games_url: str,
            nintendo_switch_url: str,
            playstation_url: str,
            google_play_store_url: str,
            apple_app_store_url: str,
            website_url: str,
        ) -> Any:
            response = graphql_client.create_game(
                name=name,
                steam_url=steam_url if len(steam_url) != 0 else None,
                epic_games_url=epic_games_url if len(epic_games_url) != 0 else None,
                nintendo_switch_url=(
                    nintendo_switch_url if len(nintendo_switch_url) != 0 else None
                ),
                playstation_url=playstation_url if len(playstation_url) != 0 else None,
                google_play_store_url=(
                    google_play_store_url if len(google_play_store_url) != 0 else None
                ),
                apple_app_store_url=(
                    apple_app_store_url if len(apple_app_store_url) != 0 else None
                ),
                website_url=website_url if len(website_url) != 0 else None,
            )
            game = response.game
            if game is None:
                raise Exception("game must not be None")

            return [
                game.id,
            ]

        clear_button.add(
            components=[
                name_text_field,
                steam_url_text_field,
                epic_games_url_text_field,
                nintendo_switch_url_text_field,
                playstation_url_text_field,
                google_play_store_url_text_field,
                apple_app_store_url_text_field,
                website_url_text_field,
                added_game_id_text_field,
            ],
        )

        add_game_button.click(
            fn=handle_add_game_button_clicked,
            inputs=[
                name_text_field,
                steam_url_text_field,
                epic_games_url_text_field,
                nintendo_switch_url_text_field,
                playstation_url_text_field,
                google_play_store_url_text_field,
                apple_app_store_url_text_field,
                website_url_text_field,
            ],
            outputs=[
                added_game_id_text_field,
            ],
        )

    return tab
