"""Install the qualified Vesper launcher on I: and arm its no-write preview."""
import argparse
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess

from attempt_archive import digest, verify_saved


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "releases/vesper-launcher-1"
BASE = "retro/d35-launcher1/"
FRONTEND = "retro/vrtemu"
MUSIC = BASE + "d35-menu.pcm"
MARKER = BASE + "vesper-preview.once"
PREVIOUS = "a5f2d4ba50c85e4b177bb96c93a0dfbbec26516cc8f52ee4d4fcda9799b1a18a"
CORE = "70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936"
installer = import_module("install-snes-raster-device")


def clean(card, archive, phase):
    installer.fix.health(archive, phase)
    result = subprocess.check_output(["fsutil", "dirty", "query", card.drive], text=True)
    (archive / f"fsutil-{phase}.txt").write_text(result, encoding="utf-8")
    assert "is not dirty" in result.lower(), result


def stage(card, archive, build):
    prior = {}
    for name in ("archive.json", "outside-retro.json"):
        metadata = json.loads((archive / name).read_text(encoding="utf-8"))
        verify_saved(archive, metadata)
        prior.update({x["path"]: x["sha256"] for x in metadata["all_retro_files"]})
    assert prior[FRONTEND] == prior[BASE+"vrtemu"] == PREVIOUS
    assert prior[BASE+"libs/d35-snes.so"] == CORE
    assert not any(Path(name).name.lower() in ("code.bkp", "armed", "vesper-preview.once") for name in prior)
    installer.verify_inventory(card, prior)
    clean(card, archive, "vesper-before")

    qualification = json.loads((build / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["arm_passed"] and qualification["physical"] is False
    for name, checksum in qualification["sources"].items():
        assert digest(ROOT/name) == checksum, name
    for name, checksum in qualification["build"].items():
        assert digest(build/name) == checksum, name
    for name, checksum in qualification["assets"].items():
        assert digest(ASSETS/name) == checksum, name

    payload = {
        BASE+"vesper-update.rgb565": (build/"vesper-update.rgb565").read_bytes(),
        BASE+"d35-transition.pcm": (ASSETS/"d35-transition.pcm").read_bytes(),
        MUSIC: (ASSETS/"d35-menu.pcm").read_bytes(),
        BASE+"vrtemu": (build/"vrtemu").read_bytes(),
        FRONTEND: (build/"vrtemu").read_bytes(),
    }
    # Retain a single rollback set containing only the changed existing files.
    rollback = archive/"changed-payload-rollback"
    rollback.mkdir()
    previous = {}
    for name in payload.keys() & prior.keys():
        data = (card/name).read_bytes()
        target = rollback/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        assert digest(target) == prior[name], name
        previous[name] = data

    expected = {name: sha256(data).hexdigest() for name, data in payload.items()}
    marker = b"vesper-preview-v1\n"
    expected[MARKER] = sha256(marker).hexdigest()
    written = []
    try:
        for name, data in payload.items():
            written.append(name)
            installer.fix.atomic(card/name, data)
        written.append(MARKER)
        installer.fix.atomic(card/MARKER, marker)
        installer.verify_inventory(card, {**prior, **expected})
        clean(card, archive, "vesper-armed")
    except BaseException:
        for name in reversed(written):
            target = card/name
            if target.exists() and digest(target) == expected[name]:
                if name in previous:
                    installer.fix.atomic(target, previous[name])
                else:
                    target.unlink()
        raise

    receipt = {
        "source_commit": installer.fix.git("rev-parse", "HEAD"),
        "payload_sha256": expected,
        "protected_files_verified": len(prior.keys()-payload.keys()),
        "card_files_verified": len(prior.keys() | expected.keys()),
        "archive": archive.name,
        "music": "M06 Start Line",
        "effect": "S07 Leaf Brush",
        "one_boot_preview": True,
        "firmware_update_armed": False,
        "fat32_clean": True,
        "physical": "pending",
    }
    (archive/"vesper-launcher-installation.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("build", type=Path)
    args = parser.parse_args()
    card = Path("I:/").resolve()
    assert str(card).lower() in ("i:/","i:\\")
    archive, build = args.archive.resolve(), args.build.resolve()
    assert archive.is_relative_to(ROOT/"device-evidence") and build.is_relative_to(ROOT/"build")
    print(json.dumps(stage(card, archive, build), indent=2))
