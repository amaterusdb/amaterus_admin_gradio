from logging import Logger
from typing import Any
from zoneinfo import ZoneInfo

import gradio as gr

from ..graphql_client import Client

JST = ZoneInfo("Asia/Tokyo")


def create_create_program_person_tab(
    graphql_client: Client,
    logger: Logger,
) -> gr.Tab:
    initial_data = graphql_client.get_create_program_person_initial_data()

    with gr.Tab(label="プログラムの参加者を追加") as tab:
        gr.Markdown("# プログラムの参加者を追加")

        with gr.Row():
            clear_field_button = gr.ClearButton(
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
                label="参加者",
                interactive=True,
                choices=list(
                    map(
                        lambda person: (person.name, person.id),
                        initial_data.person_list,
                    ),
                ),
            )
        with gr.Row():
            is_absent_radio = gr.Radio(
                label="欠席?",
                interactive=True,
                choices=[
                    ("データなし", 0),
                    ("出席", 1),
                    ("欠席", 2),
                ],
            )
        with gr.Row():
            add_program_person_button = gr.Button(
                value="プログラム参加者を追加",
                variant="primary",
            )
        with gr.Row():
            added_program_person_id_text_field = gr.Textbox(
                label="追加されたプログラム参加者のデータベース上のID",
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

            response = graphql_client.get_program_project_list_by_project_id(
                project_id=project_id,
            )
            project = response.project
            if project is None:
                raise Exception("Project must not be None")

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

        def handle_add_proram_person_button_clicked(
            program_id: str,
            person_id: str,
            is_absent_int: int,
        ) -> Any:
            is_absent: bool | None = None
            if is_absent_int == 0:
                is_absent = None
            elif is_absent_int == 1:
                is_absent = False
            elif is_absent_int == 2:
                is_absent = True

            response = graphql_client.create_program_person(
                program_id=program_id,
                person_id=person_id,
                is_absent=is_absent,
            )
            program_person = response.program_person
            if program_person is None:
                raise Exception("program_person must not be None")

            return [
                program_person.id,
            ]

        project_drop.select(
            fn=handle_project_changed,
            inputs=project_drop,
            outputs=program_drop,
        )

        clear_field_button.add(
            components=[
                project_drop,
                program_drop,
                person_drop,
                is_absent_radio,
                added_program_person_id_text_field,
            ],
        )

        add_program_person_button.click(
            fn=handle_add_proram_person_button_clicked,
            inputs=[
                program_drop,
                person_drop,
                is_absent_radio,
            ],
            outputs=[
                added_program_person_id_text_field,
            ],
        )

    return tab
