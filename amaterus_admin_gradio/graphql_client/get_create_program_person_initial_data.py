# Generated by ariadne-codegen
# Source: queries/

from typing import Any, List

from .base_model import BaseModel


class GetCreateProgramPersonInitialData(BaseModel):
    project_list: List["GetCreateProgramPersonInitialDataProjectList"]
    person_list: List["GetCreateProgramPersonInitialDataPersonList"]


class GetCreateProgramPersonInitialDataProjectList(BaseModel):
    id: Any
    name: str


class GetCreateProgramPersonInitialDataPersonList(BaseModel):
    id: Any
    name: str


GetCreateProgramPersonInitialData.model_rebuild()
