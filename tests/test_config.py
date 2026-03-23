import pytest
import json
import tempfile
from pipeline.core.config import SoftwareResolver, Config, DCCSoftware, Renderer
from pathlib import Path

# -----------------------------
# Test data
# -----------------------------

TESTS_DIR = Path(__file__).parent
TEST_CONFIGS_DIR = TESTS_DIR / "test_configs"


_COMPATIBILITY = TEST_CONFIGS_DIR / "compatibility.json"
_DEFAULTS = TEST_CONFIGS_DIR / "defaults.json"
_VALID_RESOLVED = TEST_CONFIGS_DIR / "valid_resolved.json"
_INVALID_RENDERER_VERSION = TEST_CONFIGS_DIR / "invalid_renderer_version.json"
_UNKNOWN_DCC = TEST_CONFIGS_DIR / "unknown_dcc.json"
_LIST_VERSION_ERROR = TEST_CONFIGS_DIR / "list_version_error.json"


# -----------------------------
# Pytest Fixtures
# -----------------------------


@pytest.fixture
def resolver():
    resolver = SoftwareResolver(_COMPATIBILITY, _DEFAULTS)
    return resolver


@pytest.fixture
def sample_config_file():
    """
    Create a sample config file
    """
    data = {
        "dcc_software": {
            "houdini": {"21.0.512": {"renderer": {"redshift": ["2026.2.0"]}}},
            "maya": {"2024": {"renderer": {"arnold": ["7.2", "7.3"]}}},
        }
    }

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
        json.dump(data, f)
        f.flush()
        yield Path(f.name)

    # cleanup
    Path(f.name).unlink(missing_ok=True)


# -----------------------------
# Tests
# -----------------------------


# --------- SoftwareResolver


def test_valid_configuration(resolver):
    # Should not raise
    resolver.resolve(_VALID_RESOLVED)


def test_invalid_renderer_version(resolver):
    with pytest.raises(RuntimeError, match="Incompatible renderer version:"):
        resolver.resolve(_INVALID_RENDERER_VERSION)


def test_unknown_dcc(resolver):
    with pytest.raises(RuntimeError, match="Unknown DCC"):
        resolver.resolve(_UNKNOWN_DCC)


def test_renderer_version_must_be_string(resolver):
    with pytest.raises(RuntimeError, match="Renderer versions are expected as a list"):
        resolver.resolve(_LIST_VERSION_ERROR)


# --------- Config


def test_load_config(sample_config_file):
    cfg = Config(sample_config_file)
    assert "dcc_software" in cfg.data
    assert "houdini" in cfg.get_dccs()
    assert "maya" in cfg.get_dccs()


def test_get_dcc_versions(sample_config_file):
    cfg = Config(sample_config_file)
    versions = cfg.get_dcc_versions(DCCSoftware.houdini)
    assert "21.0.512" in versions


def test_get_renderers(sample_config_file):
    cfg = Config(sample_config_file)
    renderers = cfg.get_renderers(DCCSoftware.houdini, "21.0.512")
    assert renderers == ["redshift"]


def test_get_renderer_versions(sample_config_file):
    cfg = Config(sample_config_file)
    versions = cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift)
    assert versions == ["2026.2.0"]


def test_add_renderer_version(sample_config_file):
    cfg = Config(sample_config_file)
    cfg.add_renderer_version(DCCSoftware.houdini, "21.0.512", Renderer.redshift, "2026.3.0")
    versions = cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift)
    assert "2026.3.0" in versions

    # Ensure duplicates are not added
    cfg.add_renderer_version(DCCSoftware.houdini, "21.0.512", Renderer.redshift, "2026.3.0")
    versions = cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift)
    assert versions.count("2026.3.0") == 1


def test_remove_dcc(sample_config_file):
    cfg = Config(sample_config_file)
    cfg.remove_dcc(DCCSoftware.houdini)
    assert "houdini" not in cfg.get_dccs()
    assert "maya" in cfg.get_dccs()


def test_remove_renderer_version(sample_config_file):
    cfg = Config(sample_config_file)
    cfg.remove_renderer_version(DCCSoftware.houdini, "21.0.512", Renderer.redshift, "2026.2.0")
    versions = cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift)
    assert "2026.2.0" not in versions

    # Ensure no error on removal if already removed
    cfg.add_renderer_version(DCCSoftware.houdini, "21.0.512", Renderer.redshift, "2026.3.0")
    versions = cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift)
    assert "0.0" not in versions
    cfg.remove_renderer_version(DCCSoftware.houdini, "21.0.512", Renderer.redshift, "0.0")
    versions = cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift)
    assert "0.0" not in versions


def test_save_and_reload(tmp_path):
    # Prepare config
    cfg_file = tmp_path / "config.json"
    cfg = Config(cfg_file)
    cfg.add_renderer_version(DCCSoftware.houdini, "21.0.512", Renderer.redshift, "2026.2.0")
    cfg.save()

    # Reload and check
    cfg2 = Config(cfg_file)
    assert cfg2.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.redshift) == ["2026.2.0"]


def test_missing_dcc_raises(sample_config_file):
    cfg = Config(sample_config_file)
    with pytest.raises(KeyError):
        cfg.get_dcc_versions(DCCSoftware.blender)


def test_missing_renderer_raises(sample_config_file):
    cfg = Config(sample_config_file)
    with pytest.raises(KeyError):
        cfg.get_renderer_versions(DCCSoftware.houdini, "21.0.512", Renderer.karma)


##TODO!
def test_to_schema(sample_config_file):
    cfg = Config(sample_config_file)
    assert "test" not in cfg.to_schema()
