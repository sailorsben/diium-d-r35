"""Install the reviewed launcher and covers to the D-R35 card on Windows."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

from attempt_archive import digest, verify_saved


CARD = Path("I:/")
CORE = "retro/d35-launcher1/libs/d35-snes.so"
CORE_SHA = "70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936"
LAUNCHER = "retro/vrtemu"
FALLBACK = "retro/d35-launcher1/vrtemu"
OLD_LAUNCHER = "0ed23b74500561a6faf70f267bc31b8b1192a0ab8dacf2a64e0f2d5830ae765c"
ART = "retro/d35-launcher1/ui_en.bkp"
TARGETS = {LAUNCHER, FALLBACK, ART, "002/images/Star Fox.png", "002/images/Chrono Trigger.png"}


def inventory_hashes(root):
    result = {}
    def fail(error):
        raise error
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=fail):
        for name in dirs + files:
            path = Path(parent)/name
            if path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError(f"Unexpected link: {path}")
        for name in files:
            path = Path(parent)/name
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def require_clean_card(output, when):
    check = subprocess.run(["chkdsk", "I:"], capture_output=True, text=True)
    dirty = subprocess.run(["fsutil", "dirty", "query", "I:"], capture_output=True, text=True)
    (output/f"chkdsk-{when}.txt").write_text(check.stdout+check.stderr, encoding="utf-8")
    (output/f"dirty-{when}.txt").write_text(dirty.stdout+dirty.stderr, encoding="utf-8")
    if check.returncode or "11EB-1465" not in check.stdout or "found no problems" not in check.stdout:
        raise ValueError("Read-only FAT check did not identify a clean D-R35 card")
    if dirty.returncode or "NOT Dirty" not in dirty.stdout:
        raise ValueError("D-R35 volume is dirty or could not be queried")


def stage(source, target, expected):
    temporary = target.with_name(target.name+".d35-install")
    with temporary.open("xb") as pending:
        try:
            with source.open("rb") as stream:
                shutil.copyfileobj(stream, pending)
            pending.flush()
            os.fsync(pending.fileno())
            if digest(temporary) != expected:
                raise ValueError(f"Staged readback mismatch: {target}")
        except BaseException:
            pending.close()
            temporary.unlink()
            raise
    return temporary


def install(payload, qualification, archive, output):
    candidate = json.loads(qualification.read_text(encoding="utf-8"))
    manifest = json.loads((archive/"archive.json").read_text(encoding="utf-8"))
    desired = candidate["payload_sha256"]
    if set(desired) != TARGETS or desired[LAUNCHER] != desired[FALLBACK]:
        raise ValueError("Unexpected launcher install targets")
    if not candidate["arm_checks_passed"] or candidate["core_sha256"] != CORE_SHA:
        raise ValueError("Missing launcher qualification")
    if (manifest["volume_serial"], manifest["card_writes"], manifest["fat_clean"]) != ("11EB-1465", 0, True):
        raise ValueError("Unexpected preinstall archive")
    verify_saved(archive, manifest)
    verify_saved(archive, dict(manifest, all_retro_files=manifest["outside_retro_files"]))
    for relative, sha in desired.items():
        if digest(payload/relative) != sha or (CARD/relative).with_name(Path(relative).name+".d35-install").exists():
            raise ValueError(f"Source or pending install mismatch: {relative}")
    require_clean_card(output, "preflight")
    before = {e["path"]:e["sha256"] for e in manifest["all_retro_files"]+manifest["outside_retro_files"]}
    if inventory_hashes(CARD) != before or any(before.get(p) != OLD_LAUNCHER for p in (LAUNCHER,FALLBACK)):
        raise ValueError("Card changed since collection")
    if before.get(CORE) != CORE_SHA or "retro/update/Code.bkp" in before:
        raise ValueError("Unexpected core or armed firmware update")
    for game in ("002/Star Fox.sfc","002/Chrono Trigger.zip"):
        if game not in before:
            raise ValueError(f"Missing game for thumbnail: {game}")

    rollback = output/"previous-files"
    for relative in desired:
        if relative in before:
            old = rollback/relative
            old.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(CARD/relative,old)
            if digest(old) != before[relative]:
                raise ValueError(f"Rollback copy mismatch: {relative}")

    pending = {}
    committed = []
    try:
        for relative, sha in desired.items():
            pending[relative] = stage(payload/relative,CARD/relative,sha)
        for relative in [name for name in desired if name!=LAUNCHER]+[LAUNCHER]:
            os.replace(pending[relative],CARD/relative)
            committed.append(relative)
        after = inventory_hashes(CARD)
        if after != before | desired:
            raise ValueError("Unexpected changes in postinstall card inventory")
        require_clean_card(output,"after")
    except BaseException:
        for temporary in pending.values():
            temporary.unlink(missing_ok=True)
        for relative in reversed(committed):
            target = CARD/relative
            if relative in before:
                os.replace(stage(rollback/relative,target,before[relative]),target)
            else:
                target.unlink()
        raise

    receipt = dict(archive=archive.name, source_commit=candidate["source_commit"], payload_sha256=desired,
                   verified_card_files=len(after), unchanged_card_files=len(set(after)-TARGETS),
                   retained_progress_and_log_files=sum(e["stored"] for e in manifest["all_retro_files"]+manifest["outside_retro_files"]),
                   core_sha256=CORE_SHA, fat32_clean=True, one_boot_test_armed=False,
                   spi_update_armed=False, persistent_card_launcher=True, physical_boot="pending")
    (output/"installation.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("payload","qualification","archive","output"):
        parser.add_argument(argument,type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    install(args.payload,args.qualification,args.archive,args.output)
