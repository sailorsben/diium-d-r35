"""Add the Settings shutdown action to the already armed Vesper launcher."""
import argparse
import json
from pathlib import Path

from attempt_archive import digest, verify_saved
from importlib import import_module

vesper = import_module("stage-vesper-launcher")
ROOT = vesper.ROOT
BASE = vesper.BASE
ARMING = ROOT/"evidence/2026-11-13/vesper-launcher-arming.json"
HELPER = ROOT/"build/launcher-power-off.sh"


def stage(card, archive, out):
    expected = {}
    for name in ("archive", "outside-retro"):
        metadata = json.loads((archive/f"{name}.json").read_text(encoding="utf-8"))
        verify_saved(archive, metadata)
        expected.update({e["path"]: e["sha256"] for e in metadata["all_retro_files"]})
    original = json.loads(ARMING.read_text(encoding="utf-8"))
    for name, checksum in original["payload_sha256"].items():
        assert expected[name] == checksum, name
    assert expected[BASE+"libs/d35-snes.so"] == vesper.CORE
    assert not any(Path(name).name.lower() in ("code.bkp", "armed") for name in expected)
    assert BASE+"power-off.sh" not in expected
    vesper.installer.verify_inventory(card, expected)
    vesper.clean(card, archive, "shutdown-before")

    report = json.loads((out/"qualification.json").read_text(encoding="utf-8"))
    for name, checksum in report["source_sha256"].items():
        assert digest(ROOT/name) == checksum, name
    for name, checksum in report["build_sha256"].items():
        assert digest(out/name) == checksum, name
    assert report["arm_and_shell_passed"] and not report["physical"]
    assert digest(out/"libs/d35-snes.so") == vesper.CORE
    launcher = (out/"vrtemu").read_bytes()
    old = (card/vesper.FRONTEND).read_bytes()
    rollback = archive/"changed-payload-rollback"
    rollback.mkdir()
    (rollback/"vrtemu").write_bytes(old)
    assert digest(rollback/"vrtemu") == expected[vesper.FRONTEND]
    files = {BASE+"power-off.sh": (HELPER.read_bytes().replace(b"\r\n",b"\n"), report["helper_on_card_sha256"]),
             BASE+"vrtemu": (launcher, report["build_sha256"]["vrtemu"]),
             vesper.FRONTEND: (launcher, report["build_sha256"]["vrtemu"])}
    touched = []
    try:
        for name, (data, checksum) in files.items():
            touched.append(name)
            vesper.installer.fix.atomic(card/name,data)
            assert digest(card/name) == checksum, name
        vesper.installer.verify_inventory(card,{**expected, **{n: h for n, (_, h) in files.items()}})
        vesper.clean(card, archive, "shutdown-after")
    except BaseException:
        for name in reversed(touched):
            path = card/name
            if path.exists() and digest(path) == files[name][1]:
                if name in expected:
                    vesper.installer.fix.atomic(path,old)
                else:
                    path.unlink()
        raise
    result = {
        "source_commit": vesper.installer.fix.git("rev-parse", "HEAD"),
        "changed_sha256": {n: h for n, (_, h) in files.items()},
        "verified_files": len(expected.keys() | files.keys()),
        "vesper_preview_armed": True,
        "firmware_update_armed": False,
        "fat32_clean_before_test": True,
        "physical_shutdown": "pending",
    }
    (archive/"vesper-shutdown-installation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("out",type=Path)
    args = parser.parse_args()
    archive, out = args.archive.resolve(), args.out.resolve()
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/","i:\\")
    assert archive.is_relative_to(ROOT/"device-evidence") and out.is_relative_to(ROOT/"build")
    print(json.dumps(stage(card,archive,out),indent=2))
