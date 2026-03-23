import pytest
from pipeline.core.project_manager import Project, Shot, ProductionStage
from pipeline.core.config import Renderer


# -----------------------------
# Pytest Fixtures
# -----------------------------

@pytest.fixture
def project(tmp_path, monkeypatch):
    # override global PROJECT_ROOT_DIR safely
    monkeypatch.setattr(
        "core.project_manager.PROJECT_ROOT_DIR",
        str(tmp_path),
    )

    project = Project(
        name="TEST_PROJECT",
        fps=24.0,
        houdini_version="19.5",
        renderers=[Renderer.karma],
    )
    project.create()
    return project

@pytest.fixture
def shot(project):
    shot = Shot(
        name="S010",
        project=project,
        framerange=24,
        prod_stage= ProductionStage.production
    )
    shot.create()
    return shot

# -----------------------------
# Tests
# -----------------------------

def test_project_config(project):
    #should not raise

    config = project.get_project_config()
    # assert config
    assert config["project"]["project_name"] == "TEST_PROJECT"
    assert config["project"]["fps"] == 24.0
    assert config["project"]["houdini_version"] == "19.5"
    assert config["project"]["renderers"] == [Renderer.karma]
#
# def test_shot_config(shot_maker):
#     assert project_maker().get_shot_config() not empty
#
# def test_add_shot(shot_maker):
#     shot_maker.add_shot_to_proj_config()
#     assert shot_maker.get_project_config()["shots"]
#
# def test_project_exists(project_maker):
#     # should raise an error, project already exists
#
# def test_shot_exists(shot_maker):
#     # should raise an error, shot already exists
#
#
#
