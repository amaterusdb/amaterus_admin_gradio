# Generated by ariadne-codegen on 2023-09-25 12:58
# Source: queries/

from typing import Any, List

from .base_model import BaseModel


class GetCreateProgramYoutubeVideoLiveArchiveInitialData(BaseModel):
    project_list: List["GetCreateProgramYoutubeVideoLiveArchiveInitialDataProjectList"]
    person_list: List["GetCreateProgramYoutubeVideoLiveArchiveInitialDataPersonList"]


class GetCreateProgramYoutubeVideoLiveArchiveInitialDataProjectList(BaseModel):
    id: Any
    name: str


class GetCreateProgramYoutubeVideoLiveArchiveInitialDataPersonList(BaseModel):
    id: Any
    name: str


GetCreateProgramYoutubeVideoLiveArchiveInitialData.model_rebuild()
GetCreateProgramYoutubeVideoLiveArchiveInitialDataProjectList.model_rebuild()
GetCreateProgramYoutubeVideoLiveArchiveInitialDataPersonList.model_rebuild()