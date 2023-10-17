# Generated by ariadne-codegen on 2023-10-17 18:26
# Source: queries/

from typing import Any, List

from .base_model import BaseModel


class GetCreateProgramYoutubeLiveLiveArchiveInitialData(BaseModel):
    project_list: List["GetCreateProgramYoutubeLiveLiveArchiveInitialDataProjectList"]
    person_list: List["GetCreateProgramYoutubeLiveLiveArchiveInitialDataPersonList"]


class GetCreateProgramYoutubeLiveLiveArchiveInitialDataProjectList(BaseModel):
    id: Any
    name: str


class GetCreateProgramYoutubeLiveLiveArchiveInitialDataPersonList(BaseModel):
    id: Any
    name: str


GetCreateProgramYoutubeLiveLiveArchiveInitialData.model_rebuild()
GetCreateProgramYoutubeLiveLiveArchiveInitialDataProjectList.model_rebuild()
GetCreateProgramYoutubeLiveLiveArchiveInitialDataPersonList.model_rebuild()
