"""Update the installed D-R35 grid from its verified prior card release."""

import argparse
from datetime import datetime, timezone
from importlib import import_module
import json
from pathlib import Path

from attempt_archive import digest, inventory, verify_saved, write_manifest


direct = import_module("install-direct-launcher-firmware")
ROOT = direct.ROOT
EVIDENCE = ROOT/"evidence/2026-11-13"


def stage(card, payload):
    prior = direct.read(EVIDENCE/"home-grid-arming.json")
    report = direct.read(EVIDENCE/"home-grid-order-power-qualification.json")
    assert report["arm_checks_passed"] and not report["physical"]
    for name, expected in report["source_sha256"].items():
        assert digest(ROOT/name)==expected,name
    paths = ("retro/d35-launcher1/power-dialog.rgb565", "retro/d35-launcher1/home-grid.rgb565",
             "retro/d35-launcher1/vrtemu", "retro/vrtemu")
    files = {name:(payload/Path(name).name).read_bytes() for name in paths}
    hashes = {name:direct.digest(payload/Path(name).name) for name in paths}
    assert all(hashes[name]==report["payload_sha256"][Path(name).name] for name in paths)
    archive = ROOT/"device-evidence"/("launcher-order-power-before-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    archive.mkdir()
    old = inventory(card,archive)
    outside = inventory(card,archive,outside=True)
    write_manifest(archive/"archive.json",old,all_retro_files=old,card_writes=0)
    write_manifest(archive/"outside-retro.json",outside,files=outside,card_writes=0)
    verify_saved(archive,{"schema":"sparse-attempt-v1","all_retro_files":old+outside})
    before = {entry["path"]:entry["sha256"] for entry in old+outside}
    for name, expected in prior["payload_sha256"].items():
        if name==direct.TRIGGER and name not in before:
            continue
        assert before[name]==expected,name
    assert before[direct.BASE+"libs/d35-snes.so"]==report["unchanged_core_sha256"]
    assert paths[0] not in before
    installer = direct.installer
    installer.verify_inventory(card,before)
    direct.clean(card,archive,"order-power-before")

    backups = archive/"changed-payload-rollback"
    for name in files.keys() & before.keys():
        target = backups/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((card/name).read_bytes())
        assert digest(target)==before[name],name
    touched = []
    try:
        for name, data in files.items():
            touched.append(name)
            installer.fix.atomic(card/name,data)
        installer.verify_inventory(card,{**before,**hashes})
        direct.clean(card,archive,"order-power-after")
    except BaseException:
        for name in reversed(touched):
            target = card/name
            if name in before:
                if not target.exists() or digest(target)!=before[name]:
                    installer.fix.atomic(target,(backups/name).read_bytes())
            elif target.exists() and digest(target)==hashes[name]:
                target.unlink()
        raise
    receipt = {"source_commit":installer.fix.git("rev-parse","HEAD"),"archive":archive.name,
               "payload_sha256":hashes,"verified_card_files":len(before.keys()|hashes.keys()),
               "firmware_trigger_present":direct.TRIGGER in before,
               "fat32_clean":True,"physical_verification":"pending"}
    (archive/"launcher-order-power-installation.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload",type=lambda p:Path(p).resolve())
    args = parser.parse_args()
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/","i:\\") and args.payload.is_relative_to(ROOT/"build")
    stage(card,args.payload)
