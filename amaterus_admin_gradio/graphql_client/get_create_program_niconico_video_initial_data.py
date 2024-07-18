# Generated by ariadne-codegen
# Source: queries/

from typing import Any, List

from .base_model import BaseModel


class GetCreateProgramNiconicoVideoInitialData(BaseModel):
    project_list: List["GetCreateProgramNiconicoVideoInitialDataProjectList"]
    person_list: List["GetCreateProgramNiconicoVideoInitialDataPersonList"]


class GetCreateProgramNiconicoVideoInitialDataProjectList(BaseModel):
    id: Any
    name: str


class GetCreateProgramNiconicoVideoInitialDataPersonList(BaseModel):
    id: Any
    name: str


GetCreateProgramNiconicoVideoInitialData.model_rebuild()
