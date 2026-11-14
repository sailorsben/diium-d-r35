"""Install the reviewed D-R35 grid and arm its qualified SPI boot update."""

import argparse
from importlib import import_module
import json
from pathlib import Path
import subprocess

from attempt_archive import digest, verify_saved


direct = import_module("install-direct-launcher-firmware")
ROOT = direct.ROOT
BASE = direct.BASE
TRIGGER = direct.TRIGGER
PINNED_FRONTEND = "fdde200c86ef066201212724d1a41f6c1bb7bf9dc40957a4e06cc4070e80beda"


def stage(card, archive, launcher, assets, firmware, qualification):
    installer = direct.installer
    old, outside = (direct.read(archive/f"{name}.json") for name in ("archive", "outside-retro"))
    assert old["card_writes"]==outside["card_writes"]==0
    verify_saved(archive,old)
    verify_saved(archive,{**outside,"all_retro_files":outside["files"]})
    before = {e["path"]:e["sha256"] for e in old["all_retro_files"]+outside["files"]}
    previous = direct.read(ROOT/"evidence/2026-11-13/direct-launcher-firmware-qualification.json")
    prior_themes = direct.read(ROOT/"evidence/2026-11-12/stock-shell-settings-classic-raised.json")
    pins = {
        "retro/init":previous["artifact_sha256"]["sd-init"], "retro/main":direct.SUPERVISOR,
        "retro/driver.so":direct.DRIVER, "retro/vrtemu":PINNED_FRONTEND,
        BASE+"vrtemu":PINNED_FRONTEND, BASE+"libs/d35-snes.so":prior_themes["payload_sha256"]["libs/d35-snes.so"],
        **{BASE+n:prior_themes["payload_sha256"][n] for n in ("ui_en.bkp","ui_classic.bkp")},
    }
    for path, sha in pins.items():
        assert before[path]==sha,path
    assert BASE+"home-grid.rgb565" not in before
    assert not any(Path(n).name.lower() in {"armed","code.bkp","vesper-preview.once"} for n in before)
    installer.verify_inventory(card,before)
    direct.clean(card,archive,"grid-before")
    q = direct.read(qualification)
    assert q["arm_checks_passed"] and not q["physical"]
    fw = direct.read(firmware/"preparation.json")
    assert fw["baseline_sha256"]==previous["artifact_sha256"]["expected-after-vendor.bin"]
    for name, sha in fw["artifact_sha256"].items():
        assert digest(firmware/name)==sha,name
    direct.inspect_package((firmware/"Code.bkp").read_bytes(),(firmware/"candidate.bin").read_bytes())
    assert digest(launcher/"libs/d35-snes.so")==pins[BASE+"libs/d35-snes.so"]
    payload = {
        BASE+"home-grid.rgb565":assets/"home-grid.rgb565",
        BASE+"ui_en.bkp":assets/"ui_en.bkp",
        BASE+"ui_classic.bkp":assets/"ui_classic.bkp",
        BASE+"vrtemu":launcher/"vrtemu",
        "retro/vrtemu":launcher/"vrtemu",
        TRIGGER:firmware/"Code.bkp",
    }
    for source in set(payload.values()):
        assert digest(source)==q["payload_sha256"][source.name],source
    rollback = archive/"changed-payload-rollback"
    rollback.mkdir()
    for path in payload.keys() & before.keys():
        target = rollback/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((card/path).read_bytes())
        assert digest(target)==before[path],path

    hashes = {path:q["payload_sha256"][source.name] for path,source in payload.items()}
    touched = []
    try:
        for path,source in payload.items():
            if path==TRIGGER:
                installer.verify_inventory(card,{**before,**{n:hashes[n] for n in touched}})
                direct.clean(card,archive,"grid-pre-flash-trigger")
            touched.append(path)
            installer.fix.atomic(card/path,source.read_bytes())
        expected = {**before,**hashes}
        installer.verify_inventory(card,expected)
        direct.inspect_package((card/TRIGGER).read_bytes(),(firmware/"candidate.bin").read_bytes())
        direct.clean(card,archive,"grid-armed")
    except BaseException:
        for path in reversed(touched):
            target = card/path
            if path in before:
                if not target.exists() or digest(target)!=before[path]:
                    installer.fix.atomic(target,(rollback/path).read_bytes())
            elif target.exists() and digest(target)==hashes[path]:
                target.unlink()
        raise

    receipt = {
        "archive":archive.name,
        "source_commit":installer.fix.git("rev-parse","HEAD"),
        "payload_sha256":hashes,"verified_card_files":len(expected),
        "unchanged_card_files":len(before.keys()-payload.keys()),
        "core_sha256":pins[BASE+"libs/d35-snes.so"],
        "fat32_clean":True,"persistent_card_launcher":True,
        "expected_erased_blocks":fw["expected_erased_blocks"],
        "expected_programmed_firmware_sha256":fw["artifact_sha256"]["expected-after-vendor.bin"],
        "physical_flash":"pending",
    }
    (archive/"home-grid-installation.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("archive","launcher","assets","firmware","qualification"):
        p.add_argument(name,type=lambda x:Path(x).resolve())
    a = p.parse_args()
    assert a.archive.is_relative_to(ROOT/"device-evidence") and a.firmware.is_relative_to(ROOT/"device-evidence")
    assert a.launcher.is_relative_to(ROOT/"build") and a.assets.is_relative_to(ROOT/"build")
    assert a.qualification.is_relative_to(ROOT/"evidence")
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/","i:\\")
    stage(card,a.archive,a.launcher,a.assets,a.firmware,a.qualification)
