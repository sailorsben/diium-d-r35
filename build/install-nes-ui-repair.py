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
FF2_EDGE_PAYLOAD = ROOT / "build/ff2-edge-private/vrtemu"
FF2_EDGE_SHA = "7a9bd7b76d5c57bfb065bbdef2f051b8b83282cda00fc4413d6cf29bb34f9fab"
CONTROLS_PAYLOAD = ROOT / "build/controls-monitor-private/vrtemu"
CONTROLS_SHA = "fa19a18c3a421f9a6df5b082624652697372b054ec2dd2eecb30bb8197ef507f"
EXIT_BUILD = ROOT / "build/exit-dialog-private"
EXIT_SHA = "05f087418b34d571101295c71ff55e35c13d6e1a5cfafd2e04787dcaa8b2c47a"
EXIT_ART = "retro/d35-launcher1/exit-dialog.rgb565"
EXIT_ART_SHA = "4003f2547ef182e057d9f5dd5b942195cb157a2f9cbb0db7b455c3d25e63f546"
TRACE = "retro/d35-launcher1/ff2-controls.log"
PREVIOUS_TRACE = "retro/d35-launcher1/ff2-controls.previous.log"
NES = "d8a9a87a8aabc6c290c887545247b907e2e48bd0a70f788c5f1a41db06d51fa6"
SNES = "70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936"
TARGETS = ("retro/vrtemu", "retro/d35-launcher1/vrtemu")


def install(payload=PAYLOAD, old=OLD, new=NEW, phase="nes-ui", archive=None,
            *, exit_art=None, rearm=False):
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
    if exit_art:
        assert digest(exit_art) == EXIT_ART_SHA and not (CARD / EXIT_ART).exists()

    if archive is None:
        archive = ROOT / "device-evidence" / (
            phase + "-before-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        archive.mkdir()
        retro = inventory(CARD, archive)
        outside = inventory(CARD, archive, outside=True)
        write_manifest(archive / "archive.json", retro, all_retro_files=retro, card_writes=0)
        write_manifest(archive / "outside-retro.json", outside, files=outside, card_writes=0)
    else:
        archive = archive.resolve()
        assert archive.parent == ROOT / "device-evidence"
        retro = json.loads((archive / "archive.json").read_text())["all_retro_files"]
        outside = json.loads((archive / "outside-retro.json").read_text())["files"]
    verify_saved(archive, {"schema": "sparse-attempt-v1", "all_retro_files": retro+outside})
    before = {e["path"]: e["sha256"] for e in retro+outside}
    direct.installer.verify_inventory(CARD, before)
    direct.clean(CARD, archive, phase + "-before")
    if rearm:
        assert PREVIOUS_TRACE not in before and digest(archive / TRACE) == before[TRACE]

    # Both executable paths have the same verified original.
    rollback = archive / "changed-payload-rollback/vrtemu"
    rollback.parent.mkdir(parents=True, exist_ok=True)
    if not rollback.exists():
        rollback.write_bytes((CARD / TARGETS[0]).read_bytes())
    assert digest(rollback) == old
    replacements = dict.fromkeys(TARGETS, payload.read_bytes())
    expected = dict(before)
    expected.update({name: new for name in TARGETS})
    if exit_art:
        replacements = {EXIT_ART: exit_art.read_bytes(), **replacements}
        expected[EXIT_ART] = EXIT_ART_SHA
    atomic = direct.installer.fix.atomic
    # The shared atomic writer uses this adjacent scratch file. Check ownership
    # before staging so a failed write can be cleaned up and safely retried.
    scratch = {name: (CARD / (name + ".uart-fix-tmp")) for name in replacements}
    assert all(not path.exists() for path in scratch.values())
    touched = []
    rotated = False
    try:
        for name, data in replacements.items():
            touched.append(name)
            atomic(CARD / name, data)
        if rearm:
            (CARD / TRACE).rename(CARD / PREVIOUS_TRACE)
            rotated = True
            expected[PREVIOUS_TRACE] = expected.pop(TRACE)
        direct.installer.verify_inventory(CARD, expected)
        direct.clean(CARD, archive, phase + "-after")
    except BaseException:
        if rotated:
            (CARD / PREVIOUS_TRACE).rename(CARD / TRACE)
        for name in reversed(touched):
            scratch[name].unlink(missing_ok=True)
            if name not in before:
                (CARD / name).unlink(missing_ok=True)
            elif digest(CARD / name) != old:
                atomic(CARD / name, rollback.read_bytes())
        raise

    receipt = {
        "archive": archive.name, "source_commit": direct.installer.fix.git("rev-parse", "HEAD"),
        "before_sha256": old, "after_sha256": new, "changed_paths": list(replacements),
        "verified_card_files": len(expected), "core_and_rom_files_changed": False,
        "new_sparse_content_bytes": sum(e["new_content_bytes"] for e in retro+outside),
        "fat32_clean": True, "physical_boot_and_ff2_visual": "pending",
    }
    if exit_art:
        receipt["exit_art_sha256"] = EXIT_ART_SHA
        receipt["physical_exit_dialog"] = "pending"
    if rearm:
        receipt["controls_capture_rearmed"] = True
        receipt["previous_capture"] = PREVIOUS_TRACE
        receipt["previous_capture_sha256"] = before[TRACE]
    (archive / (phase + "-installation.json")).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    builds = parser.add_mutually_exclusive_group()
    builds.add_argument("--viewport-receipt", action="store_true")
    builds.add_argument("--chaos-rush-edges", action="store_true")
    builds.add_argument("--controls-monitor", action="store_true")
    builds.add_argument("--exit-dialog", action="store_true")
    parser.add_argument("--rearm-controls", action="store_true",
                        help="Retain the collected FF2 trace under a new name and enable the next capture")
    parser.add_argument("--return-archive", type=Path, help="Previously collected card return for input monitoring")
    args = parser.parse_args()
    if args.return_archive and not (args.controls_monitor or args.exit_dialog):
        parser.error("--return-archive requires --controls-monitor or --exit-dialog")
    if args.rearm_controls and not args.exit_dialog:
        parser.error("--rearm-controls requires --exit-dialog")
    if args.exit_dialog:
        install(EXIT_BUILD / "arm/vrtemu", CONTROLS_SHA, EXIT_SHA, "exit-dialog", args.return_archive,
                exit_art=EXIT_BUILD / "exit-dialog.rgb565", rearm=args.rearm_controls)
    elif args.controls_monitor:
        install(CONTROLS_PAYLOAD, FF2_EDGE_SHA, CONTROLS_SHA, "controls", args.return_archive)
    elif args.chaos_rush_edges:
        install(FF2_EDGE_PAYLOAD, RECEIPT_SHA, FF2_EDGE_SHA, "ff2-vertical-edges")
    elif args.viewport_receipt:
        install(RECEIPT_PAYLOAD, NEW, RECEIPT_SHA, "nes-viewport")
    else:
        install()
