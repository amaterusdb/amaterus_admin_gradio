# Generated by ariadne-codegen on 2023-09-24 20:09
# Source: queries/

from typing import Any, List, Optional

from .base_model import BaseModel


class GetProgramProjectListByProjectId(BaseModel):
    project: Optional["GetProgramProjectListByProjectIdProject"]


class GetProgramProjectListByProjectIdProject(BaseModel):
    program_project_list: List[
        "GetProgramProjectListByProjectIdProjectProgramProjectList"
    ]


class GetProgramProjectListByProjectIdProjectProgramProjectList(BaseModel):
    program: "GetProgramProjectListByProjectIdProjectProgramProjectListProgram"


class GetProgramProjectListByProjectIdProjectProgramProjectListProgram(BaseModel):
    id: Any
    title: str


GetProgramProjectListByProjectId.model_rebuild()
GetProgramProjectListByProjectIdProject.model_rebuild()
GetProgramProjectListByProjectIdProjectProgramProjectList.model_rebuild()
GetProgramProjectListByProjectIdProjectProgramProjectListProgram.model_rebuild()
