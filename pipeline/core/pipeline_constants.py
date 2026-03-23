from pathlib import Path
from enum import Enum

# =============================================================================
# ROOTS & FOLDERS
# =============================================================================
PROJECT_ROOT_DIR = Path("C:/pipeline/server/projects")
PROJECT_STRUCTURE = [
    "00_CONFIG",
    "01_PRODUCING",
    "02_BRIEF",
    "03_FROM_CLIENT",
    "04_TO_CLIENT",
    "05_DAILIES",
    "06_FOOTAGE",
    "07_AUDIO",
    "08_PRODUCTION",
    "99_MASTER",
]

PROD_SUBDIRS = ["ASSETS", "SHOTS", "EDIT"]
DEPARTMENT_STRUCTURE = ["data", "geo", "tex", "tools", "usd", "workfiles", "published", "cache", "render", "wip"]
SHOT_STRUCTURE = {
    "config": [],
    "data": [],
    "footage": [],
    "previs": [],
    "layout": DEPARTMENT_STRUCTURE,
    "animation": DEPARTMENT_STRUCTURE,
    "fx": DEPARTMENT_STRUCTURE,
    "lighting": DEPARTMENT_STRUCTURE,
    "precomp": DEPARTMENT_STRUCTURE,
    "comp": DEPARTMENT_STRUCTURE,
}


# =============================================================================
# ENUMS
# =============================================================================


class DCCSoftware(Enum):
    houdini = "houdini"
    maya = "maya"
    blender = "blender"


class Renderer(Enum):
    karma = "karma"
    redshift = "redshift"
    arnold = "arnold"


class ProductionStage(Enum):
    production = "production"
    preproduction = "preproduction"


# =============================================================================
# NAMING RULES / CONVENTIONS
# =============================================================================

SHOT_NAME_PREFIX = "SH_"
PROJECT_NAME_MIN_LENGTH = 2
PREVIS_SHOT_NAME_PREFIX = "previs_SH_"
