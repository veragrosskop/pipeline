import enum
from pathlib import Path
import os as os
from typing import List, Optional, Tuple

from pipeline.core.config import Renderer, DCCSoftware, Config
from pipeline.core.logger import pipeline_logger
from pipeline.core.schemas import ProjectSchema
from pipeline.core.pipeline_constants import (
    ProductionStage,
    PROJECT_ROOT_DIR,
    PROJECT_STRUCTURE,
    PROD_SUBDIRS,
    SHOT_STRUCTURE,
)

## TODO add previs functionality in an elegant way -> renaming/reordering shots after previs, seperate versioning etc


# =============================================================================
# Shot Class
# =============================================================================
class Shot:
    def __init__(
        self,
        name: str,
        project: "Project",
        framerange: Optional[Tuple[int, int]] = None,
        prod_stage: ProductionStage = ProductionStage.production,
    ):
        self.name = name
        self._project = project
        self.config: Optional[Config] = None  ##TODO! initialize elegantly
        self.framerange = framerange or (1001, 1100)
        self.prod_stage = prod_stage
        self.path: Optional[Path] = None

    @property
    def project(self) -> "Project":
        """Read only project object"""
        return self._project

    def create(self):
        """Create shot folders and config."""
        self._create_shot_dir()
        self._write_config()
        self.project.add_shot_to_project(self)

    def _create_shot_dir(self):
        """create shot directory unless it already exists"""

        if self.prod_stage == ProductionStage.production:
            production_dir = [
                pdir for pdir in self._project.path.iterdir() if pdir.is_dir() and pdir.name.endswith("_PRODUCTION")
            ]
            if not production_dir:
                raise FileExistsError(f"production dir in {self.project.path} does not exist.")
            production_dir = production_dir[0]
            pipeline_logger.info(f"found production folder: {production_dir}")
            self.path = Path(os.path.join(production_dir, "SHOTS", self.name))
            self.path.mkdir(exist_ok=True, parents=True)  ## TODO add safety checks -> no overwrite etc

            for key, value in SHOT_STRUCTURE.items():
                # create folder for current key
                current_path = Path(os.path.join(self.path, key))
                current_path.mkdir(exist_ok=True, parents=True)  ## TODO add safety checks -> no overwrite etc

                if isinstance(value, list) and len(value) > 0:
                    for item in value:
                        (current_path / item).mkdir(exist_ok=True, parents=True)

        elif self.prod_stage == ProductionStage.preproduction:
            # do something
            ...

        pipeline_logger.info(f"Created shot directory: {self.path}")

    def _write_config(self):
        """write shot config file"""
        config_path = Path(os.path.join(self.path, "00_CONFIG"))
        self.config = Config(config_path)
        self.config.update_shot_info(self.name, self._project.name, self.framerange)
        pipeline_logger.info(f"Created {config_path}")


# =============================================================================
# Project Class
# =============================================================================
class Project:
    def __init__(
        self,
        name: str,
        fps: float,
        config: Optional[Config] = None,
        force: bool = False,
    ):
        self.name = name
        self.fps = fps
        self.config: Optional[Config] = config
        self.force = force
        self.path = None
        self.shots: List[Shot] = []
        self.config_path = None

    def create(self):
        """Create project folder structure and config."""
        self._create_project_dir()
        self._init_project_folders()
        self._set_config_path()
        self._write_config()
        pipeline_logger.info(f"Created project: {self.name}")

    @classmethod
    def load(cls, project_path: Path) -> "Project":
        """load existing project from config file"""

        config_path = project_path / "00_CONFIG" / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"No config found for project at {project_path}")

        config = Config(config_path)
        schema = ProjectSchema(
            **{
                "name": project_path.name,  # or config.data["info"].get("project_name"),
                "fps": config.data.get("info").get("fps"),  ##TODO handle default frame ranges
                "config": config.to_schema(),
            }
        )

        project = cls(
            name=schema.name,
            fps=schema.fps,
            config=config,
        )
        project.path = project_path
        return project

    def _create_project_dir(self):
        """create project directory unless it already exists"""
        self.path = Path(PROJECT_ROOT_DIR) / self.name
        self.path.mkdir(exist_ok=True, parents=True)
        pipeline_logger.info(f"Created project dir: {self.path}")

    def _init_project_folders(self):
        """initialize project folders"""

        if not self.path.exists():
            raise FileExistsError(f"{self.path} does not exists.")

        for folder in PROJECT_STRUCTURE:
            path = Path(os.path.join(self.path, folder))
            path.mkdir(exist_ok=True, parents=True)

            if folder.endswith("PREVIS") or folder.endswith("PRODUCTION"):
                for subdir in PROD_SUBDIRS:
                    path = Path(os.path.join(self.path, folder, subdir))
                    path.mkdir(exist_ok=True, parents=True)

        pipeline_logger.info(f"Initialized project folders")

    def _set_config_path(self):
        """set config file path"""
        path = Path(os.path.join(self.path, "00_CONFIG"))
        self.config_path = path / "config.json"
        pipeline_logger.info(f"Defined the config path at: {self.config_path}")

    ##TODO move config writing and reading to config.py and use helper functions from there? Make a class?
    def _write_config(self):
        """write config to json file at self.config_path"""

        self.config = Config(self.config_path)
        self.config.update_project_info(self.name, self.fps, self.shots)
        pipeline_logger.info(f"Created {self.config_path}")

    def add_shot_to_project(self, shot: Shot):
        """add shot to self.shots and add name to project config info"""

        self.shots.append(shot)
        shot_names = [shot.name for shot in self.shots]
        self.config.update_project_info(self.name, self.fps, shot_names)
        pipeline_logger.info(f"Added {shot.name} to project")

    def remove_shot_from_project(self, shot: Shot):
        """remove shot config from project folder"""

        if shot in self.shots:
            try:
                self.shots.remove(shot)
                shot_names = [shot.name for shot in self.shots]
                self.config.update_project_info(self.name, self.fps, shot_names)
                pipeline_logger.info(f"Removed {shot.name} from project")
            except ValueError:
                pipeline_logger.error(f"Tried to remove {shot.name} from project, but was not able.")

        else:
            pipeline_logger.warning(f"Tried to remove {shot.name} from project, but was not found.")


#     ##TODO add functionality for previs shot numbers and shot name validation
