"""Install the qualified interactive Star Fox audio test on I: for one boot."""

import argparse
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess

from attempt_archive import digest, verify_saved


ROOT = Path(__file__).resolve().parent.parent
BASE = "retro/d35-launcher1/"
MARKERS = (BASE+"armed", "retro/snes-mvp/armed")
DEVICE_DRIVER = "2c0134b3fc425f5b65c271c014e291824590c773190014f4e50c3ed33c2f13f9"
QUALIFICATION = ROOT/"evidence/2026-11-12/starfox-launcher-audio-qualification.json"
THEMES = ROOT/"evidence/2026-11-12/stock-shell-settings-theme-arming.json"
installer = import_module("install-snes-raster-device")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def clean(card, archive, label):
    installer.fix.health(archive, label)
    dirty = subprocess.check_output(["fsutil", "dirty", "query", str(card.drive)], text=True)
    (archive/f"fsutil-{label}.txt").write_text(dirty, encoding="utf-8")
    assert "is not dirty" in dirty.lower(), dirty


def verify_unarmed(card):
    assert not list(card.rglob("armed")) and not list(card.rglob("Code.bkp"))


def inventory(archive):
    inside, outside = read(archive/"archive.json"), read(archive/"outside-retro.json")
    assert inside["fat_clean"] and inside["card_writes"] == outside["card_writes"] == 0
    verify_saved(archive, inside)
    verify_saved(archive, dict(outside, all_retro_files=outside["files"]))
    return {entry["path"]:entry["sha256"] for entry in inside["all_retro_files"]+outside["files"]}


def stage(card, archive, package):
    before = inventory(archive)
    verify_unarmed(card)
    installer.verify_inventory(card, before)
    themes = read(THEMES)
    for name, sha in themes["payload_sha256"].items():
        if name not in MARKERS:
            assert before[name] == sha, name
    assert before["retro/driver.so"] == DEVICE_DRIVER
    assert before["retro/init"] == "b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7"

    q = read(QUALIFICATION)
    assert q["arm_checks_passed"] and not q["physical"]
    for name, sha in q["source_sha256"].items():
        assert digest(ROOT/name) == sha, name
    for name, sha in q["payload_sha256"].items():
        assert digest(package/name) == sha, name
    for name in ("d35-menu.pcm", "ui_en.bkp", "ui_classic.bkp", "libs/d35-snes.so", "launch.sh"):
        assert before[BASE+name] == q["payload_sha256"][name], name

    git = installer.fix.git
    source = git("rev-parse", "HEAD")
    assert source == git("rev-parse", "origin/codex/snes-mvp-foundation")
    assert not git("status", "--porcelain")
    clean(card, archive, "starfox-before")

    changed = ("vrtemu", "libs/d35-starfox-audio.so")
    marker = f"d35-launcher1 starfox-native150 {source}\n".encode()
    payload = {BASE+name:(package/name).read_bytes() for name in changed}
    payload.update(dict.fromkeys(MARKERS, marker))
    rollback = archive/"changed-payload-rollback/vrtemu"
    rollback.parent.mkdir()
    rollback.write_bytes((card/(BASE+"vrtemu")).read_bytes())
    assert digest(rollback) == before[BASE+"vrtemu"]
    assert BASE+"libs/d35-starfox-audio.so" not in before

    hashes = {BASE+name:q["payload_sha256"][name] for name in changed}
    touched = []
    try:
        for name in (*hashes, *MARKERS):
            if name == MARKERS[0]:
                installer.verify_inventory(card, {**before, **hashes})
            touched.append(name)
            installer.fix.atomic(card/name, payload[name])
        hashes.update(dict.fromkeys(MARKERS, sha256(marker).hexdigest()))
        expected = {**before, **hashes}
        installer.verify_inventory(card, expected)
        assert {p.relative_to(card).as_posix() for p in card.rglob("armed")} == set(MARKERS)
        clean(card, archive, "starfox-armed")
        result = dict(source_commit=source, archive=archive.name, fat_clean=True,
            verified_card_files=len(expected), unchanged_prior_files=len(before)-1,
            payload_sha256=hashes, boot_markers=list(MARKERS), physical_result="pending",
            qualification_sha256=digest(QUALIFICATION))
        (archive/"starfox-launcher-installation.json").write_text(
            json.dumps(result, indent=2)+"\n", encoding="utf-8")
    except BaseException:
        for name in reversed(touched):
            path = card/name
            if path.exists() and digest(path) == sha256(payload[name]).hexdigest():
                if name == BASE+"vrtemu":
                    installer.fix.atomic(path, rollback.read_bytes())
                else:
                    path.unlink()
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/", "i:\\")
    archive, package = args.archive.resolve(), args.package.resolve()
    assert archive.is_relative_to(ROOT/"device-evidence")
    assert package.is_relative_to(ROOT/"build")
    stage(card, archive, package)
