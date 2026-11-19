"""Archive I: and install the verified NES/UI launcher without changing cores or ROMs."""
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
import argparse
import json

from attempt_archive import digest, inventory, verify_saved, write_manifest

direct = import_module("install-direct-launcher-firmware")
ROOT = Path(__file__).resolve().parent.parent
CARD = Path("I:/").resolve()
PAYLOAD = ROOT / "build/launcher-fixes-private-v3/vrtemu"
OLD = "4575af08eda0243f35573c833c8faa3b4b9e7c8783738b4b11bf9344819718ab"
NEW = "83c4229403df0e11ba4dd7fa8f2b824b3af38b7d50faef9d69dc0f43f39928ae"
RECEIPT_PAYLOAD = ROOT / "build/nes-receipt-private/vrtemu"
RECEIPT_SHA = "014e04d6c718652125d51a21c6ed57013003cf3f10ef3b91b11a9bb268766896"
NES = "d8a9a87a8aabc6c290c887545247b907e2e48bd0a70f788c5f1a41db06d51fa6"
SNES = "70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936"
TARGETS = ("retro/vrtemu", "retro/d35-launcher1/vrtemu")


def install(payload=PAYLOAD, old=OLD, new=NEW, phase="nes-ui"):
    assert str(CARD).lower() in ("i:/", "i:\\")
    assert digest(payload) == new
    assert not list((CARD / "retro").rglob("armed"))
    assert not (CARD / "retro/update/Code.bkp").exists()
    boot = (CARD / "retro/d35-launcher1/direct-boot.log").read_text()
    assert "firmware=direct-launcher-grid-v2" in boot
    assert "frontend=/usr/retro/vrtemu" in boot
    assert digest(CARD / "retro/libs/emu_nes.so") == NES
    assert digest(CARD / "retro/d35-launcher1/libs/d35-snes.so") == SNES
    assert digest(CARD / "retro/driver.so") == direct.DRIVER
    assert all(digest(CARD / name) == old for name in TARGETS)

    archive = ROOT / "device-evidence" / (
        phase + "-before-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    archive.mkdir()
    retro = inventory(CARD, archive)
    outside = inventory(CARD, archive, outside=True)
    write_manifest(archive / "archive.json", retro, all_retro_files=retro, card_writes=0)
    write_manifest(archive / "outside-retro.json", outside, files=outside, card_writes=0)
    verify_saved(archive, {"schema": "sparse-attempt-v1", "all_retro_files": retro+outside})
    before = {e["path"]: e["sha256"] for e in retro+outside}
    direct.installer.verify_inventory(CARD, before)
    direct.clean(CARD, archive, phase + "-before")

    # Only the two executable copies are rollback payloads. Static files are
    # represented by hashes; unique logs and progress were saved above.
    rollback = archive / "changed-payload-rollback/vrtemu"
    rollback.parent.mkdir(parents=True)
    rollback.write_bytes((CARD / TARGETS[0]).read_bytes())
    assert digest(rollback) == old
    data = payload.read_bytes()
    atomic = direct.installer.fix.atomic
    touched = []
    try:
        for name in TARGETS:
            touched.append(name)
            atomic(CARD / name, data)
        direct.installer.verify_inventory(CARD, {**before, **{n: new for n in TARGETS}})
        direct.clean(CARD, archive, phase + "-after")
    except BaseException:
        for name in reversed(touched):
            if digest(CARD / name) != old:
                atomic(CARD / name, rollback.read_bytes())
        raise

    receipt = {
        "archive": archive.name, "source_commit": direct.installer.fix.git("rev-parse", "HEAD"),
        "before_sha256": old, "after_sha256": new, "changed_paths": TARGETS,
        "verified_card_files": len(before), "core_and_rom_files_changed": False,
        "new_sparse_content_bytes": sum(e["new_content_bytes"] for e in retro+outside),
        "fat32_clean": True, "physical_boot_and_ff2_visual": "pending",
    }
    (archive / (phase + "-installation.json")).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--viewport-receipt", action="store_true")
    if parser.parse_args().viewport_receipt:
        install(RECEIPT_PAYLOAD, NEW, RECEIPT_SHA, "nes-viewport")
    else:
        install()
