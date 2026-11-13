"""Stage the qualified permanent launcher and firmware trigger on I:."""

import argparse
from importlib import import_module
import io
import json
from pathlib import Path
import subprocess
import zipfile

from attempt_archive import digest, verify_saved


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT/"evidence/2026-11-13/direct-launcher-firmware-qualification.json"
PACKAGE = ROOT/"build/stock-shell-refresh-private/launcher-settings-classic-raised-v1"
THEMES = ROOT/"evidence/2026-11-12/stock-shell-settings-classic-raised.json"
EXPERIMENT = ROOT/"evidence/2026-11-12/starfox-launcher-audio-arming.json"
TRIGGER = "retro/update/Code.bkp"
FRONTEND = "retro/vrtemu"
INIT = "retro/init"
BASE = "retro/d35-launcher1/"
STOCK = "8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72"
STOCK_INIT = "b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7"
SUPERVISOR = "ace334d88d013240e2b93eb8cb691f1f09e4109d6d509648a5518cbae0b25873"
DRIVER = "2c0134b3fc425f5b65c271c014e291824590c773190014f4e50c3ed33c2f13f9"
installer = import_module("install-snes-raster-device")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def clean(card, archive, phase):
    installer.fix.health(archive,phase)
    result = subprocess.check_output(["fsutil","dirty","query",card.drive],text=True)
    (archive/f"fsutil-{phase}.txt").write_text(result,encoding="utf-8")
    assert "is not dirty" in result.lower(),result


def inspect_package(blob, candidate):
    assert blob[:3] == b"WQW" and len(candidate) == 8388608
    with zipfile.ZipFile(io.BytesIO(blob[3:])) as archive:
        assert archive.namelist() == ["SPI_ROM.bin"] and archive.testzip() is None
        assert archive.read("SPI_ROM.bin") == candidate


def stage(card, archive, firmware):
    old, outside = read(archive/"archive.json"), read(archive/"outside-retro.json")
    assert old["filesystem_scan_clean"] and old["card_writes"] == outside["card_writes"] == 0
    verify_saved(archive,old)
    verify_saved(archive,dict(outside,all_retro_files=outside["files"]))
    before = {x["path"]:x["sha256"] for x in old["all_retro_files"]+outside["files"]}
    for path, checksum in {INIT:STOCK_INIT,FRONTEND:STOCK,"retro/main":SUPERVISOR,"retro/driver.so":DRIVER}.items():
        assert before[path] == checksum,path
    assert not list(card.rglob("Code.bkp")) and not list(card.rglob("armed"))
    installer.verify_inventory(card,before)

    q = read(EVIDENCE)
    assert q["arm_checks_passed"] and not q["physical"]
    for name, checksum in q["source_sha256"].items():
        assert digest(ROOT/name) == checksum,name
    for name, checksum in q["artifact_sha256"].items():
        assert digest(firmware/name) == checksum,name
    themes = read(THEMES)["payload_sha256"]
    for name in ("libs/d35-snes.so","d35-menu.pcm","ui_en.bkp","ui_classic.bkp"):
        assert before[BASE+name] == themes[name],name
    assert digest(PACKAGE/"vrtemu") == themes["vrtemu"]
    assert before[BASE+"vrtemu"] == read(EXPERIMENT)["payload_sha256"][BASE+"vrtemu"]
    git = installer.fix.git
    source = git("rev-parse","HEAD")
    assert source == git("rev-parse","origin/codex/snes-mvp-foundation")
    assert not git("status","--porcelain")
    clean(card,archive,"direct-launcher-before")

    candidate = (firmware/"candidate.bin").read_bytes()
    trigger = (firmware/"Code.bkp").read_bytes()
    inspect_package(trigger,candidate)
    payload = {FRONTEND:(PACKAGE/"vrtemu").read_bytes(),
               BASE+"vrtemu":(PACKAGE/"vrtemu").read_bytes(),
               INIT:(firmware/"sd-init").read_bytes(),TRIGGER:trigger}
    previous = {name:(card/name).read_bytes() for name in payload if name in before}
    rollback = archive/"changed-payload-rollback"
    rollback.mkdir()
    for name, data in previous.items():
        target = rollback/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        assert digest(target) == before[name],name
    hashes = {FRONTEND:themes["vrtemu"],BASE+"vrtemu":themes["vrtemu"],
              INIT:q["artifact_sha256"]["sd-init"],TRIGGER:q["artifact_sha256"]["Code.bkp"]}

    update = card/"retro/update"
    created_update = not update.exists()
    update.mkdir(exist_ok=True)
    touched = []
    try:
        for name, data in payload.items():
            if name == TRIGGER:
                installer.verify_inventory(card,{**before,**{n:hashes[n] for n in touched}})
                clean(card,archive,"direct-launcher-payload")
            touched.append(name)
            installer.fix.atomic(card/name,data)
        expected = {**before,**hashes}
        installer.verify_inventory(card,expected)
        inspect_package((card/TRIGGER).read_bytes(),candidate)
        assert not list(card.rglob("armed"))
        clean(card,archive,"direct-launcher-armed")
        receipt = {"source_commit":source,"archive":archive.name,"payload_sha256":hashes,
                   "unchanged_prior_files":len(before)-len(previous),"verified_card_files":len(expected),
                   "expected_programmed_firmware_sha256":q["artifact_sha256"]["expected-after-vendor.bin"],
                   "expected_erased_blocks":q["expected_erased_blocks"],"fat_clean":True,
                   "persistent_launcher":True,"one_shot_markers":False,"physical_flash":"pending"}
        (archive/"direct-launcher-installation.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    except BaseException:
        for name in reversed(touched):
            path = card/name
            if path.exists() and digest(path) == hashes[name]:
                if name in previous:
                    installer.fix.atomic(path,previous[name])
                else:
                    path.unlink()
        if created_update and not any(update.iterdir()):
            update.rmdir()
        raise
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("firmware",type=Path)
    args = parser.parse_args()
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/","i:\\")
    archive, firmware = args.archive.resolve(), args.firmware.resolve()
    assert all(p.is_relative_to(ROOT/"device-evidence") for p in (archive,firmware))
    stage(card,archive,firmware)
