"""补丁脚本的回归测试：用合成 jar 验证覆盖、注入、幂等与备份。

不碰真实的上游 jar，跑得很快。
"""
from __future__ import annotations

import importlib.util
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "patch_jar.py"

ENTRIES = {
    "BOOT-INF/classes/static/admin/index.html": (
        '<!doctype html><head><meta name="theme-color" content="#1677ff"></head>'
        "<body><div id=\"root\"></div></body>"
    ),
    "BOOT-INF/classes/static/console/index.html": "OLD CONSOLE",
    "BOOT-INF/classes/static/console/styles.css": "OLD CSS",
    "BOOT-INF/classes/static/selfdesk-brand.js": "OLD BRAND",
    "BOOT-INF/classes/static/selfdesk-admin-dash.js": "OLD DASH",
    "BOOT-INF/classes/static/keep.txt": "untouched",
}


def build_jar(path: pathlib.Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in ENTRIES.items():
            zf.writestr(name, content)


def load_module():
    spec = importlib.util.spec_from_file_location("patch_jar", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(jar: pathlib.Path, name: str) -> str:
    with zipfile.ZipFile(jar) as zf:
        return zf.read(name).decode("utf-8")


def test_patch_overwrites_and_injects(monkeypatch, tmp_path):
    jar = tmp_path / "bytedesk-starter.jar"
    build_jar(jar)
    monkeypatch.setenv("SELFDESK_JAR", str(jar))

    load_module().main()

    console = read(jar, "BOOT-INF/classes/static/console/index.html")
    assert "OLD" not in console and "SelfDesk" in console

    brand = read(jar, "BOOT-INF/classes/static/selfdesk-brand.js")
    assert "OLD BRAND" not in brand
    # 没有 .selfdesk-autologin.json 时绝不注入凭据
    assert "window.__SELFDESK_AUTOLOGIN__={" not in brand

    admin = read(jar, "BOOT-INF/classes/static/admin/index.html")
    assert 'src="/selfdesk-brand.js"' in admin
    assert "#0E7A68" in admin
    assert "#1677ff" not in admin

    assert read(jar, "BOOT-INF/classes/static/keep.txt") == "untouched"


def test_backup_created(monkeypatch, tmp_path):
    jar = tmp_path / "bytedesk-starter.jar"
    build_jar(jar)
    monkeypatch.setenv("SELFDESK_JAR", str(jar))

    load_module().main()

    assert jar.with_suffix(".jar.bak-selfdesk").exists()


def test_idempotent(monkeypatch, tmp_path):
    jar = tmp_path / "bytedesk-starter.jar"
    build_jar(jar)
    monkeypatch.setenv("SELFDESK_JAR", str(jar))

    module = load_module()
    module.main()
    module.main()

    admin = read(jar, "BOOT-INF/classes/static/admin/index.html")
    assert admin.count("selfdesk-brand.js") == 1
