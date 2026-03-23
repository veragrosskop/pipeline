import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QListWidget,
    QLineEdit,
    QSpinBox,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QCheckBox,
)

from pydantic import ValidationError

from pipeline.core.project_manager import (
    Project,
    Shot,
    PROJECT_ROOT_DIR,
    ProductionStage,
)
from pipeline.core.config import Config, DCCSoftware, Renderer
from pipeline.core.schemas import ProjectSchema, ShotSchema

# =============================================================================
# Helpers
# =============================================================================


def list_projects():
    root = Path(PROJECT_ROOT_DIR)
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def list_shots(project_path: Path):
    shots_dir = project_path / "08_PRODUCTION" / "SHOTS"
    if not shots_dir.exists():
        return []
    return sorted(p.name for p in shots_dir.iterdir() if p.is_dir())


def show_error(parent, message: str):
    QMessageBox.critical(parent, "Validation Error", message)


# =============================================================================
# DCC Selector (raw data only, no disk writes)
# =============================================================================


class DCCSelector(QWidget):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config

        layout = QHBoxLayout(self)

        self.dcc_cb = QComboBox()
        self.dcc_version_cb = QComboBox()
        self.renderer_cb = QComboBox()
        self.renderer_version_cb = QComboBox()

        layout.addWidget(self.dcc_cb)
        layout.addWidget(self.dcc_version_cb)
        layout.addWidget(self.renderer_cb)
        layout.addWidget(self.renderer_version_cb)

        self.dcc_cb.addItems([d.value for d in DCCSoftware])
        self.renderer_cb.addItems([r.value for r in Renderer])

        self.dcc_cb.currentTextChanged.connect(self._dcc_changed)
        self.renderer_cb.currentTextChanged.connect(self._renderer_changed)

        self._dcc_changed(self.dcc_cb.currentText())

    def _dcc_changed(self, _):
        self.dcc_version_cb.clear()
        self.dcc_version_cb.addItems(["latest"])

    def _renderer_changed(self, _):
        self.renderer_version_cb.clear()
        self.renderer_version_cb.addItems(["latest"])

    def collect(self):
        """Mutates in-memory Config only"""
        self.config.add_dcc_version(
            dcc=DCCSoftware(self.dcc_cb.currentText()),
            dcc_version=self.dcc_version_cb.currentText(),
            renderer=Renderer(self.renderer_cb.currentText()),
            renderer_version=self.renderer_version_cb.currentText(),
        )


# =============================================================================
# New Project Dialog
# =============================================================================


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")

        self.config = Config(Path("TEMP"))  # in-memory only

        layout = QFormLayout(self)

        self.name_le = QLineEdit()
        self.fps_sb = QSpinBox()
        self.fps_sb.setRange(1, 240)
        self.fps_sb.setValue(24)

        self.dcc_selector = DCCSelector(self.config)

        layout.addRow("Project Name", self.name_le)
        layout.addRow("FPS", self.fps_sb)
        layout.addRow("DCC / Renderer", self.dcc_selector)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_raw_data(self):
        self.dcc_selector.collect()
        return {
            "name": self.name_le.text(),
            "fps": self.fps_sb.value(),
            "config": self.config,
        }


# =============================================================================
# New Shot Dialog
# =============================================================================


class NewShotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Shot")

        self.config = Config(Path("TEMP"))

        layout = QFormLayout(self)

        self.name_le = QLineEdit()

        self.production_cb = QCheckBox("Production Shot")
        self.production_cb.setChecked(True)

        self.start_sb = QSpinBox()
        self.end_sb = QSpinBox()
        self.start_sb.setValue(1001)
        self.end_sb.setValue(1100)

        self.fps_sb = QSpinBox()
        self.fps_sb.setValue(24)

        self.dcc_selector = DCCSelector(self.config)

        layout.addRow("Shot Name", self.name_le)
        layout.addRow("Production", self.production_cb)
        layout.addRow("Frame Start", self.start_sb)
        layout.addRow("Frame End", self.end_sb)
        layout.addRow("FPS", self.fps_sb)
        layout.addRow("DCC / Renderer", self.dcc_selector)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_raw_data(self):
        self.dcc_selector.collect()
        stage = ProductionStage.production if self.production_cb.isChecked() else ProductionStage.preproduction
        return {
            "name": self.name_le.text(),
            "framerange": (self.start_sb.value(), self.end_sb.value()),
            "fps": self.fps_sb.value(),
            "stage": stage,
            "config": self.config,
        }


# =============================================================================
# Main Launcher
# =============================================================================


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Launcher")
        self.resize(520, 600)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"PROJECT ROOT: {PROJECT_ROOT_DIR}"))

        self.project_cb = QComboBox()
        self.project_cb.addItems(list_projects())
        self.project_cb.currentTextChanged.connect(self.refresh_shots)

        layout.addWidget(QLabel("PROJECT"))
        layout.addWidget(self.project_cb)

        self.add_project_btn = QPushButton("Add New Project")
        self.add_project_btn.clicked.connect(self.add_project)
        layout.addWidget(self.add_project_btn)

        layout.addWidget(QLabel("SHOTS"))
        self.shot_list = QListWidget()
        layout.addWidget(self.shot_list)

        self.add_shot_btn = QPushButton("Add New Shot")
        self.add_shot_btn.clicked.connect(self.add_shot)
        layout.addWidget(self.add_shot_btn)

        self.refresh_shots()

    # ------------------------------------------------------------------

    def refresh_shots(self):
        self.shot_list.clear()
        name = self.project_cb.currentText()
        if not name:
            return
        for shot in list_shots(Path(PROJECT_ROOT_DIR) / name):
            self.shot_list.addItem(shot)

    # ------------------------------------------------------------------

    def add_project(self):
        dlg = NewProjectDialog(self)
        if not dlg.exec():
            return

        raw = dlg.get_raw_data()

        try:
            schema = ProjectSchema(
                name=raw["name"],
                fps=raw["fps"],
                config=raw["config"].to_schema(),
            )
        except ValidationError as e:
            show_error(self, str(e))
            return

        project = Project(
            name=schema.name,
            fps=schema.fps,
        )
        project.create()
        raw["config"].save()

        self.project_cb.addItem(schema.name)

    # ------------------------------------------------------------------

    def add_shot(self):
        project_name = self.project_cb.currentText()
        if not project_name:
            return

        # load project config from disk into Project instance
        project = None
        project_path = Path(PROJECT_ROOT_DIR) / project_name
        try:
            project = Project.load(project_path)
        except Exception as e:
            print(f"Error loading project {project_name}: {e}")

        if not project:
            show_error(self, f"Project {project_name} not loaded")
            return

        dlg = NewShotDialog(self)
        if not dlg.exec():
            return

        raw = dlg.get_raw_data()

        try:
            schema = ShotSchema(
                name=raw["name"],
                framerange=raw["framerange"],
                fps=raw["fps"],
                stage=raw["stage"],
                config=raw["config"].to_schema(),
            )
        except ValidationError as e:
            show_error(self, str(e))
            return

        shot = Shot(
            name=schema.name,
            project=project,
            framerange=schema.framerange,
            prod_stage=schema.stage,
        )
        shot.create()
        raw["config"].save()

        self.refresh_shots()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Launcher()
    win.show()
    sys.exit(app.exec())
