import enum
import json
from pathlib import Path
from typing import Dict, List, Optional

from pygments.plugin import find_plugin_styles

from pipeline.core.logger import pipeline_logger
from pipeline.houdini.checks import renderer
from pipeline.core.schemas import DCCConfigSchema, DCCSchema, RendererSchema


class Renderer(enum.Enum):
    karma = "karma"
    redshift = "redshift"
    arnold = "arnold"


class DCCSoftware(enum.Enum):
    houdini = "houdini"
    maya = "maya"
    blender = "blender"


class Config:
    """
    This class wraps any config writing and reading functionality.
    It also offers helper functions for quickly accessing values from a config file.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: Dict = {}

        if self.path.exists():
            self.load()
        else:
            self.data = {"info": {}, "dcc_software": {}}

    def load(self) -> None:
        """Loads the data from a config file located at self.path into self.data as a dictionary."""
        try:
            with self.path.open("r", encoding="utf-8") as f:
                self.data = json.load(f)
                pipeline_logger.info("Config file loaded.")
        except FileNotFoundError:
            pipeline_logger.error(f"Config file not found at: {self.path}")
            raise

    def save(self) -> None:
        """Saves the dictionary data to a config json file located at self.path."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, sort_keys=True)
        except FileNotFoundError:
            pipeline_logger.error("Config file could not be saved")
            raise

    # ---- GETTERS

    def get_dccs(self) -> List[str]:
        """returns a list of all DCCs available in the config file, for example: [houdini, maya, blender]"""
        return list(self.data.get("dcc_software", {}).keys())

    def get_dcc_versions(self, dcc: DCCSoftware) -> List[str]:
        """Returns a list of all the versions of a given DCC software in this config, for example: ['21.0.512']."""
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        return list(self._dcc(dcc).keys())

    def get_renderers(self, dcc: DCCSoftware, dcc_version: str) -> List[str]:
        """Returns a list of all the renderers of a given DCC software in this config, for example: ['redshift']."""
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        try:
            return list(self._renderer_root(dcc, dcc_version).keys())
        except KeyError:
            pipeline_logger.error(f"renderer: {renderer.value} is not in the config.")
            raise

    def get_renderer_versions(self, dcc: DCCSoftware, dcc_version: str, renderer: Renderer) -> List[str]:
        """
        Returns a list of all the renderer versions of a given DCC software and renderer in this config,
        for example: ['2026.8.0', '2026.2.0'].
        """
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        if not isinstance(renderer, Renderer):
            raise TypeError(f"renderer must be Renderer enum, got {renderer!r}")
        try:
            return self._renderer_root(dcc, dcc_version)[renderer.value]
        except KeyError:
            pipeline_logger.error(f"renderer: {renderer.value} is not in the config.")
            raise

    # ---- CONFIG INFO ADD
    def update_shot_info(self, shotname: str, projectname: str, framerange: tuple):
        """Adds the shot attributes to the config file and data under info"""

        info = {}
        info["shot_name"] = shotname
        info["project_name"] = projectname
        info["shot_range"] = framerange

        # save data
        self.data["info"] = info
        self.save()
        pipeline_logger.info(f"saved info: {info}")

    def update_project_info(self, projectname: str, fps: float, shots: List[str]):
        """Adds the project attributes to the config file and data under info"""

        info = {}
        info["project_name"] = projectname
        info["fps"] = fps
        info["shots"] = shots

        # save data
        self.data["info"] = info
        self.save()
        pipeline_logger.info(f"saved info: {info}")

    # ---- DCC ADD

    def add_dcc_version(
        self,
        dcc: DCCSoftware,
        dcc_version: str,
        renderer: Renderer,
        renderer_version: str,
    ) -> None:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        if not isinstance(renderer, Renderer):
            raise TypeError(f"renderer must be Renderer enum, got {renderer!r}")
        self._ensure_nested_renderer(dcc, dcc_version, renderer)
        self.add_renderer_version(dcc, dcc_version, renderer, renderer_version)

    def add_renderer_version(
        self,
        dcc: DCCSoftware,
        dcc_version: str,
        renderer: Renderer,
        renderer_version: str,
    ) -> None:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        if not isinstance(renderer, Renderer):
            raise TypeError(f"renderer must be Renderer enum, got {renderer!r}")

        self._ensure_nested_renderer(dcc, dcc_version, renderer)
        renderer_versions = self._renderer_root(dcc, dcc_version).setdefault(renderer.value, [])

        if renderer_version not in renderer_versions:
            renderer_versions.append(renderer_version)
        elif renderer_version in renderer_versions:
            pipeline_logger.warning(f"renderer_version {renderer_version} already exists in config")

    # ---- REMOVAL FUNCTIONALITY

    def remove_dcc(self, dcc: DCCSoftware) -> None:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")

        removed = self.data.get("dcc_software", {}).pop(dcc.value, None)
        if removed is None:
            pipeline_logger.warning(f"DCC '{dcc.value}' not found in config")

    def remove_dcc_version(self, dcc: DCCSoftware, dcc_version: str) -> None:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")

        dcc_dict = self.data.get("dcc_software", {}).get(dcc.value)
        if not dcc_dict:
            pipeline_logger.warning(f"DCC '{dcc.value}' not found in config")
            return

        removed = dcc_dict.pop(dcc_version, None)
        if removed is None:
            pipeline_logger.warning(f"{dcc.value} version '{dcc_version}' not found")

        # cleanup empty DCC
        if not dcc_dict:
            self.data["dcc_software"].pop(dcc.value)

    def remove_renderer(self, dcc: DCCSoftware, dcc_version: str, renderer: Renderer) -> None:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        if not isinstance(renderer, Renderer):
            raise TypeError(f"renderer must be Renderer enum, got {renderer!r}")

        # check if dcc version has renderers
        try:
            renderer_dict = self._renderer_root(dcc, dcc_version)
        except KeyError:
            pipeline_logger.warning(f"No renderer config found for {dcc.value} {dcc_version}")
            return

        # remove the renderer if available
        removed = renderer_dict.pop(renderer.value, None)
        if removed is None:
            pipeline_logger.warning(f"Renderer '{renderer.value}' not found for {dcc.value} {dcc_version}")

    def remove_renderer_version(
        self, dcc: DCCSoftware, dcc_version: str, renderer: Renderer, renderer_version: str
    ) -> None:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        if not isinstance(renderer, Renderer):
            raise TypeError(f"renderer must be Renderer enum, got {renderer!r}")

        # check if dcc version has renderers
        try:
            versions = self._renderer_root(dcc, dcc_version).get(renderer.value)
        except KeyError:
            pipeline_logger.warning(f"No renderer config found for {dcc.value} {dcc_version} for {renderer.value}")
            return

        if versions is None or renderer_version not in versions:
            pipeline_logger.warning(
                f"Renderer version '{renderer_version}' not found for " f"{dcc.value} {dcc_version} {renderer.value}"
            )
            return

        versions.remove(renderer_version)
        # if the renderer has no versions / empty list, remove renderer
        if not versions:
            pipeline_logger.warning(f"Renderer '{renderer.value}' has no more versions in config.")

    def to_schema(self):
        """reads the config data from self.data and converts it to a schema format."""
        ##TODO! write a test for this

        dccs = []
        for dcc_name, versions in self.data.get("dcc_software", {}).items():
            renderer_versions = {}
            for dcc_version, payload in versions.items():
                renderers = []
                for r_name, r_versions in payload.get("renderer", {}).items():
                    renderers.append(
                        RendererSchema(
                            renderer=Renderer(r_name).value,
                            versions=r_versions,
                        )
                    )
                renderer_versions[dcc_version] = renderers

            dccs.append(
                DCCSchema(
                    dcc=DCCSoftware(dcc_name).value,
                    versions=renderer_versions,
                )
            )

        return DCCConfigSchema(dccs=dccs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_nested_renderer(
        self,
        dcc: DCCSoftware,
        dcc_version: str,
        renderer: Renderer,
    ) -> list[str]:
        """Helper function that adds the empty dictionaries for keys dcc_software and renderer if they don't exist."""
        return (
            self.data.setdefault("dcc_software", {})
            .setdefault(dcc.value, {})
            .setdefault(dcc_version, {})
            .setdefault("renderer", {})
            .setdefault(renderer.value, [])
        )

    def _dcc(self, dcc: DCCSoftware) -> Dict:
        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        try:
            return self.data["dcc_software"][dcc.value]
        except KeyError:
            raise KeyError(f"DCC '{dcc}' not found in config")

    def _renderer_root(self, dcc: DCCSoftware, dcc_version: str) -> Dict:
        """Helper function that gives you the dictionary of renderers for a dcc version.
        for example: {'redshift': ['2026.8.0', '2026.2.0']}"""

        if not isinstance(dcc, DCCSoftware):
            raise TypeError(f"dcc must be DCCSoftware enum, got {dcc!r}")
        try:
            return self.data["dcc_software"][dcc.value][dcc_version]["renderer"]
        except KeyError as exc:
            raise KeyError(f"Renderer config not found for: " f"{dcc} version: {dcc_version}") from exc


class SoftwareResolver:
    """Resolves and validates software versions accross the whole pipeline.
    Can validate priorities between global defaults -> project -> shot configs,
    where shot configs have the highest priority."""

    PIPELINE_CONFIG = Path("C:/pipeline/config")

    def __init__(
        self,
        compatibility_path: Optional[Path] = None,
        defaults_path: Optional[Path] = None,
    ):

        # defaults to pipeline default config unless explicitly given
        compatibility_path = compatibility_path or self.PIPELINE_CONFIG / "compatibility.json"
        defaults_path = defaults_path or self.PIPELINE_CONFIG / "defaults.json"

        self.compatibility_cfg = Config(compatibility_path)
        self.defaults_cfg = Config(defaults_path)

    def resolve(
        self,
        project_cfg_path: Optional[Path] = None,
        shot_cfg_path: Optional[Path] = None,
    ) -> Config:
        """
        Takes the default config values and sets it as the config. Let's a project config overwrite these values.
        Then lets a shot config overwrite these values. Unspecified values are passed.
        """
        project_cfg = Config(project_cfg_path) if project_cfg_path else None
        shot_cfg = Config(shot_cfg_path) if shot_cfg_path else None

        resolved_cfg = self.defaults_cfg
        if project_cfg:
            resolved_cfg = self._update_cfg(resolved_cfg, project_cfg)
        if shot_cfg:
            resolved_cfg = self._update_cfg(resolved_cfg, shot_cfg)

        self._validate(resolved_cfg)
        return resolved_cfg

    def _update_cfg(self, prev_cfg, update_cfg):
        """
        Takes a previous config (prev_cfg) and merges it with an update cfg instruction.

        Merge rules:
        - unspecified config keys are preserved from prev config
        - specified config keys are replaced if specified
        """
        ##
        # TODO!

    def _validate(self, resolved_cfg: Config) -> None:
        compat_dccs = self.compatibility_cfg.get_dccs()
        resolved_dccs = resolved_cfg.get_dccs()

        # find compatible dccs
        for dcc_name in resolved_dccs:
            if dcc_name not in compat_dccs:
                raise RuntimeError(f"Unknown DCC software: {dcc_name}")

            # validate version of dcc
            dcc = DCCSoftware(dcc_name)
            compat_versions = self.compatibility_cfg.get_dcc_versions(dcc)
            resolved_versions = resolved_cfg.get_dcc_versions(dcc)
            for dcc_version in resolved_versions:
                if dcc_version not in compat_versions:
                    raise RuntimeError(f"Unsupported {dcc_name} version: {dcc_version}")

                # validate renderer
                compat_renderer = self.compatibility_cfg.get_renderers(dcc, dcc_version)
                resolved_renderers = resolved_cfg.get_renderers(dcc, dcc_version)
                for renderer_name in resolved_renderers:
                    if renderer_name not in compat_renderer:
                        raise RuntimeError(
                            f"Unsupported {dcc_name} " f"version: {dcc_version} " f"renderer: {renderer_name}"
                        )

                    # validate renderer version
                    renderer = Renderer(renderer_name)
                    compat_ren_versions = self.compatibility_cfg.get_renderer_versions(dcc, dcc_version, renderer)
                    resolved_ren_versions = resolved_cfg.get_renderer_versions(dcc, dcc_version, renderer)
                    for ren_version in resolved_ren_versions:
                        if ren_version not in compat_ren_versions:
                            raise RuntimeError(
                                f"Incompatible renderer version:\n"
                                f"{dcc_name} is not compatible with:\n"
                                f"{renderer_name} version: {ren_version}.\n"
                                f"valid {renderer_name} versions are: {compat_ren_versions}"
                            )

    def get_default_dcc_version(self, dcc):
        """Returns the default dcc version for a given dcc according to the default config."""

    @staticmethod
    def _load_config(path):
        cfg = Config(path)
        data = cfg.data

        return data
