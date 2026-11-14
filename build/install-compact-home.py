"""Install the permanent compact Home on a returned grid-v2 D-R35 card."""

from datetime import datetime, timezone
from hashlib import sha256
from importlib import import_module
import argparse
import json
from pathlib import Path
import re

from attempt_archive import digest, inventory, verify_saved, write_manifest


direct = import_module("install-direct-launcher-firmware")
ROOT, BASE, TRIGGER = direct.ROOT, direct.BASE, direct.TRIGGER
EVIDENCE = ROOT / "evidence/2026-11-13"
BOOT_LOG = BASE + "direct-boot.log"
MARKERS = {"armed", "code.bkp", "vesper-preview.once"}


def install_launcher_update(card, payload, update):
    baseline, art_names = {
        "launcher-pause-battery": ("compact-home", ("ui_en.bkp", "ui_classic.bkp")),
        "launcher-scroll-settings": ("launcher-pause-battery", ("power-dialog.rgb565",)),
        "launcher-settings-icons": ("launcher-scroll-settings", ()),
    }[update]
    scrolling = update == "launcher-scroll-settings"
    icons = update == "launcher-settings-icons"
    qualification_dir = EVIDENCE.parent / "2026-11-14" if icons else EVIDENCE
    prior = direct.read(EVIDENCE / (baseline + "-installation.json"))
    grid = direct.read(EVIDENCE / "home-grid-arming.json")
    qualified = direct.read(qualification_dir / (update + "-qualification.json"))
    boot = direct.read(EVIDENCE / "direct-launcher-firmware-qualification.json")
    assert qualified["arm_checks_passed"] and not qualified["physical"]
    for name, expected in qualified["source_sha256"].items():
        assert digest(ROOT / name) == expected, name

    art = tuple(BASE + name for name in art_names)
    targets = (*art, BASE + "vrtemu", direct.FRONTEND)
    data = {name: (payload / Path(name).name).read_bytes() for name in targets}
    hashes = {name: sha256(blob).hexdigest() for name, blob in data.items()}
    qualified_hashes = {"vrtemu": qualified["launcher_sha256"]} if icons else qualified["payload_sha256"]
    assert all(hashes[name] == qualified_hashes[Path(name).name] for name in targets)
    if icons:
        assert qualified["unchanged_core_sha256"] == prior["core_sha256"]

    archive = ROOT / "device-evidence" / (
        update + "-before-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    archive.mkdir()
    entries = inventory(card, archive)
    outside = inventory(card, archive, outside=True)
    write_manifest(archive / "archive.json", entries, all_retro_files=entries, card_writes=0)
    write_manifest(archive / "outside-retro.json", outside, files=outside, card_writes=0)
    verify_saved(archive, {"schema": "sparse-attempt-v1", "all_retro_files": entries + outside})
    before = {entry["path"]: entry["sha256"] for entry in entries + outside}
    pins = {
        BASE + "ui_en.bkp": grid["payload_sha256"][BASE + "ui_en.bkp"],
        BASE + "ui_classic.bkp": grid["payload_sha256"][BASE + "ui_classic.bkp"],
        **prior["payload_sha256"], BASE + "libs/d35-snes.so": prior["core_sha256"],
        direct.INIT: boot["artifact_sha256"]["sd-init"],
        "retro/main": direct.SUPERVISOR, "retro/driver.so": direct.DRIVER,
    }
    if scrolling or icons:
        compact = direct.read(EVIDENCE / "compact-home-installation.json")
        pins[BASE + "home-grid.rgb565"] = compact["payload_sha256"][BASE + "home-grid.rgb565"]
        if scrolling:
            pins[BASE + "power-dialog.rgb565"] = compact["payload_sha256"][BASE + "power-dialog.rgb565"]
    if icons:
        # The pause update refreshed both theme packs after Home was installed.
        pause = direct.read(EVIDENCE / "launcher-pause-battery-installation.json")
        for asset in ("ui_en.bkp", "ui_classic.bkp"):
            pins[BASE + asset] = pause["payload_sha256"][BASE + asset]
    for name, expected in pins.items():
        assert before.get(name) == expected, name
    assert not any(Path(n).name.lower() in MARKERS or n.lower().endswith(".armed") for n in before)
    log = dict(line.split("=", 1) for line in (archive / BOOT_LOG).read_text().splitlines())
    assert log.get("firmware") == "direct-launcher-grid-v2" and log.get("layout") == "grid"
    assert log.get("frontend") == "/usr/retro/vrtemu"
    assert re.fullmatch(r"[0-9a-f-]{36}", log.get("boot_id", ""))
    verify = direct.installer.verify_inventory
    direct.clean(card, archive, update + "-before")

    rollback = archive / "changed-payload-rollback"
    for name in targets:
        path = rollback / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((card / name).read_bytes())
        assert digest(path) == before[name], name

    atomic = direct.installer.fix.atomic
    touched = []
    music_dir = card / (BASE + "music")
    created_music_dir = False
    try:
        for name, blob in data.items():
            touched.append(name)
            atomic(card / name, blob)
        if scrolling and not music_dir.exists():
            music_dir.mkdir()
            created_music_dir = True
        if scrolling:
            assert music_dir.is_dir()
        verify(card, {**before, **hashes})
        direct.clean(card, archive, update + "-after")
    except BaseException:
        if created_music_dir:
            music_dir.rmdir()
        for name in reversed(touched):
            target = card / name
            if not target.exists() or digest(target) != before[name]:
                atomic(target, (rollback / name).read_bytes())
        raise

    receipt = {
        "archive": archive.name, "source_commit": direct.installer.fix.git("rev-parse", "HEAD"),
        "payload_sha256": hashes, "verified_card_files": len(before),
        "unchanged_card_files": len(before) - len(targets),
        "retained_progress_and_log_files": sum(e["stored"] for e in entries + outside),
        "core_sha256": prior["core_sha256"], "returned_boot_id": log["boot_id"],
        "spi_update_armed": False, "one_boot_test_armed": False, "fat32_clean": True,
        "persistent_card_launcher": True, "new_launcher_physical_boot": "pending",
    }
    body = json.dumps(receipt, indent=2) + "\n"
    (archive / (update + "-installation.json")).write_text(body, encoding="utf-8")
    print(body, end="")


def install(card, payload):
    prior = direct.read(EVIDENCE / "home-grid-arming.json")
    qualified = direct.read(EVIDENCE / "compact-home-qualification.json")
    firmware = direct.read(EVIDENCE / "direct-launcher-firmware-qualification.json")
    assert qualified["arm_checks_passed"] and not qualified["physical"]
    for name, expected in qualified["source_sha256"].items():
        assert digest(ROOT / name) == expected, name

    files = {BASE + "power-dialog.rgb565": "power-dialog.rgb565",
             BASE + "home-grid.rgb565": "home-grid.rgb565",
             BASE + "vrtemu": "vrtemu", direct.FRONTEND: "vrtemu"}
    data = {name: (payload / filename).read_bytes() for name, filename in files.items()}
    hashes = {name: sha256(blob).hexdigest() for name, blob in data.items()}
    assert all(hashes[n] == qualified["payload_sha256"][files[n]] for n in files)

    archive = ROOT / "device-evidence" / (
        "compact-home-before-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    archive.mkdir()
    entries = inventory(card, archive)
    outside = inventory(card, archive, outside=True)
    write_manifest(archive / "archive.json", entries, all_retro_files=entries, card_writes=0)
    write_manifest(archive / "outside-retro.json", outside, files=outside, card_writes=0)
    verify_saved(archive, {"schema": "sparse-attempt-v1", "all_retro_files": entries + outside})
    before = {entry["path"]: entry["sha256"] for entry in entries + outside}
    pins = {**prior["payload_sha256"], BASE + "libs/d35-snes.so": prior["core_sha256"],
            direct.INIT: firmware["artifact_sha256"]["sd-init"],
            "retro/main": direct.SUPERVISOR, "retro/driver.so": direct.DRIVER}
    for name, expected in pins.items():
        assert before.get(name) == expected, name
    assert files.keys() - before.keys() == {BASE + "power-dialog.rgb565"}
    assert {n for n in before if Path(n).name.lower() in MARKERS or n.lower().endswith(".armed")} == {TRIGGER}
    log = dict(line.split("=", 1) for line in (archive / BOOT_LOG).read_text().splitlines())
    assert log.get("firmware") == "direct-launcher-grid-v2"
    assert log.get("frontend") == "/usr/retro/vrtemu" and log.get("layout") == "grid"
    assert re.fullmatch(r"[0-9a-f-]{36}", log.get("boot_id", ""))
    verify = direct.installer.verify_inventory
    verify(card, before)
    direct.clean(card, archive, "compact-home-before")

    rollback = archive / "changed-payload-rollback"
    for name in (files.keys() & before.keys()) | {TRIGGER}:
        path = rollback / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((card / name).read_bytes())
        assert digest(path) == before[name], name

    atomic = direct.installer.fix.atomic
    touched = []
    expected = {**before, **hashes}
    del expected[TRIGGER]
    try:
        for name, blob in data.items():
            touched.append(name)
            atomic(card / name, blob)
        touched.append(TRIGGER)
        (card / TRIGGER).unlink()
        verify(card, expected)
        direct.clean(card, archive, "compact-home-after")
    except BaseException:
        for name in reversed(touched):
            target = card / name
            if name in before:
                if not target.exists() or digest(target) != before[name]:
                    atomic(target, (rollback / name).read_bytes())
            elif target.exists():
                assert digest(target) == hashes[name], name
                target.unlink()
        raise

    receipt = {
        "archive": archive.name, "source_commit": direct.installer.fix.git("rev-parse", "HEAD"),
        "payload_sha256": hashes, "verified_card_files": len(expected),
        "unchanged_card_files": len(before.keys() - files.keys() - {TRIGGER}),
        "retained_progress_and_log_files": sum(e["stored"] for e in entries + outside),
        "new_private_archive_bytes": sum(e["new_content_bytes"] for e in entries + outside),
        "core_sha256": before[BASE + "libs/d35-snes.so"],
        "board_handoff": log["firmware"], "returned_boot_id": log["boot_id"],
        "consumed_firmware_package_archived_sha256": before[TRIGGER],
        "spi_update_armed": False, "one_boot_test_armed": False, "fat32_clean": True,
        "persistent_card_launcher": True, "new_grid_physical_boot": "pending",
    }
    body = json.dumps(receipt, indent=2) + "\n"
    (archive / "compact-home-installation.json").write_text(body, encoding="utf-8")
    print(body, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=lambda p: Path(p).resolve())
    update = parser.add_mutually_exclusive_group()
    update.add_argument("--pause-battery", action="store_true")
    update.add_argument("--scroll-settings", action="store_true")
    update.add_argument("--settings-icons", action="store_true")
    args = parser.parse_args()
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/", "i:\\") and args.payload.is_relative_to(ROOT / "build")
    if args.settings_icons:
        install_launcher_update(card, args.payload, "launcher-settings-icons")
    elif args.scroll_settings:
        install_launcher_update(card, args.payload, "launcher-scroll-settings")
    elif args.pause_battery:
        install_launcher_update(card, args.payload, "launcher-pause-battery")
    else:
        install(card, args.payload)
