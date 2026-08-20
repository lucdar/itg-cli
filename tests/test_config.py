from pathlib import Path

import pytest
from itg_cli._config import CLISettings, ConfigError

CONFIG_TEMPLATE = """version = 1

[required]
root = '{root}'
singles_pack_name = 'Singles'
delete_macos_files = false

[optional]
downloads = ''
packs = ''
courses = ''
cache = ''
"""


@pytest.fixture
def itg_root(tmp_path: Path) -> Path:
    root = tmp_path / "ITGmania"
    for sub in ["Songs", "Courses", "Cache"]:
        (root / sub).mkdir(parents=True)
    return root


def write_config(tmp_path: Path, content: str) -> Path:
    cfg = tmp_path / "config.toml"
    cfg.write_text(content)
    return cfg


def test_valid_config(tmp_path, itg_root):
    cfg = write_config(tmp_path, CONFIG_TEMPLATE.format(root=itg_root))
    settings = CLISettings(cfg)
    assert settings.root == itg_root
    assert settings.packs == itg_root / "Songs"
    assert settings.courses == itg_root / "Courses"
    assert settings.cache == itg_root / "Cache"
    assert settings.singles == itg_root / "Songs" / "Singles"
    assert settings.downloads is None
    assert settings.delete_macos_files is False


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        CLISettings(tmp_path / "nonexistent.toml")


def test_empty_root_raises(tmp_path):
    cfg = write_config(tmp_path, CONFIG_TEMPLATE.format(root=""))
    with pytest.raises(ConfigError, match="root"):
        CLISettings(cfg)


def test_missing_table_raises(tmp_path):
    cfg = write_config(tmp_path, "version = 1\n[required]\nroot = '/tmp'\n")
    with pytest.raises(ConfigError, match="optional"):
        CLISettings(cfg)


def test_nonexistent_dirs_raise(tmp_path):
    cfg = write_config(
        tmp_path, CONFIG_TEMPLATE.format(root=tmp_path / "nowhere")
    )
    with pytest.raises(ConfigError, match="Invalid fields"):
        CLISettings(cfg)


def test_write_default(tmp_path, itg_root, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Default Linux root is ~/.itgmania; point it at our fake install
    itgmania = tmp_path / ".itgmania"
    itg_root.rename(itgmania)
    cfg_path = tmp_path / "config" / "config.toml"
    settings = CLISettings(cfg_path, write_default=True)
    assert cfg_path.is_file()
    assert settings.root == itgmania
    assert settings.packs == itgmania / "Songs"
