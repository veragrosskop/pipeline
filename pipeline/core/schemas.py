from typing import Dict, List, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator

from pipeline.core.pipeline_constants import DCCSoftware, Renderer, ProductionStage

# =============================================================================
# DCC CONFIG SCHEMA
# =============================================================================


class RendererSchema(BaseModel):
    renderer: Renderer
    versions: List[str]

    @field_validator("versions")
    @classmethod
    def versions_not_empty(cls, v):
        if not v:
            raise ValueError("Renderer must have at least one version")
        return v


class DCCSchema(BaseModel):
    dcc: DCCSoftware
    versions: Dict[str, List[RendererSchema]]

    @model_validator(mode="after")
    def validate_versions(self):
        if not self.versions:
            raise ValueError(f"{self.dcc.value} must define at least one version")
        return self


class DCCConfigSchema(BaseModel):
    dccs: List[DCCSchema]

    @model_validator(mode="after")
    def validate_unique_dccs(self):
        dcc_names = [d.dcc for d in self.dccs]
        if len(dcc_names) != len(set(dcc_names)):
            raise ValueError("Duplicate DCC entries detected")
        return self


# =============================================================================
# PROJECT SCHEMA
# =============================================================================


class ProjectSchema(BaseModel):
    name: str = Field(min_length=2)
    fps: float = Field(gt=0, le=240)
    config: DCCConfigSchema

    @field_validator("name")
    @classmethod
    def no_spaces(cls, v):
        if " " in v:
            raise ValueError("Project name may not contain spaces")
        return v


# =============================================================================
# SHOT SCHEMA
# =============================================================================


class ShotSchema(BaseModel):
    name: str
    framerange: Tuple[int, int]
    fps: float
    stage: ProductionStage
    config: DCCConfigSchema

    @field_validator("framerange")
    @classmethod
    def valid_framerange(cls, v):
        start, end = v
        if start >= end:
            raise ValueError("Frame range start must be smaller than end")
        return v

    @field_validator("name")
    @classmethod
    def valid_shot_name(cls, v):
        if " " in v:
            raise ValueError("Shot name may not contain spaces")
        return v
