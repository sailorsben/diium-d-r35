"""Execute the generated startup tails with the original firmware BusyBox."""

import argparse
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent
SHELL = ["qemu-arm", "-0", "busybox", "-L", str(ROOT/"build/sysroot"),
         str(ROOT/"build/uart-fix-private/firmware-busybox"), "sh"]


def check(prepared):
    board = (prepared/"init.project.rc").read_text().split("if [ -f /usr/retro/init ];then\n",1)[1]
    board = "if [ -f /usr/retro/init ];then\n" + board
    card = (prepared/"sd-init").read_text()
    anchor = '  # First update boot still runs under the old firmware.\n'
    card = card.split(anchor,1)[1].split("  /usr/retro/main &",1)[0]
    with TemporaryDirectory() as path:
        fixture = Path(path)
        retro, proc, tmp = (fixture/name for name in ("retro","proc","tmp"))
        for directory in (retro/"d35-launcher1/libs", proc/"sys/kernel/random", proc/"42", tmp):
            directory.mkdir(parents=True)
        for file in (retro/"init",retro/"vrtemu",retro/"d35-launcher1/libs/d35-snes.so"):
            file.touch()
            file.chmod(0o755)
        (proc/"sys/kernel/random/boot_id").write_text("boot-fixture-1\n")
        comm, status = proc/"42/comm", proc/"42/status"
        comm.write_text("showlogo\n")
        log = retro/"d35-launcher1/direct-boot.log"
        stop, ready = tmp/"vrtemu.log", tmp/"d35-direct-launcher.ready"
        events = fixture/"events"

        def invoke(source, code=0):
            paths = {"/usr/retro":str(retro),"/proc/":str(proc)+"/","/tmp/":str(tmp)+"/"}
            source = re.sub(r"/usr/retro|/proc/|/tmp/",lambda m:paths[m[0]],source)
            source = source.replace("@EVENTS@",str(events))
            source = "sleep() { :; }\n" + source + "\nwait\n"
            result = subprocess.run(SHELL,input=source,text=True,capture_output=True,timeout=10)
            assert result.returncode==code,(result.returncode,result.stderr)

        board = board.replace("/wdt &",":").replace("/usr/retro/init &","echo card >> @EVENTS@")
        board = board.replace("modprobe joydev",":").replace("/system/bin/vrtemu &","echo fallback >> @EVENTS@")
        card += "echo supervisor >> @EVENTS@\n"

        # Old firmware reaches the same splash gate through the SD init.
        status.write_text("State:\tS (sleeping)\n")
        invoke(card,1)
        assert stop.exists() and not events.exists() and not ready.exists()
        status.write_text("State:\tZ (zombie)\n")
        invoke(card)
        assert events.read_text()=="supervisor\n"
        events.unlink()

        # Flashed firmware waits, records a boot identity, then enters SD init.
        status.write_text("State:\tS (sleeping)\n")
        invoke(board,1)
        assert not ready.exists() and not log.exists() and not events.exists()
        status.write_text("State:\tZ (zombie)\n")
        invoke(board)
        grid = "firmware=direct-launcher-grid-v2" in board
        tag = "direct-launcher-grid-v2" if grid else "direct-launcher-v1"
        assert ready.read_text()==f"firmware={tag}\n"
        assert "boot_id=boot-fixture-1\n" in log.read_text() and events.read_text()=="card\n"
        if grid:
            assert "layout=stock\n" in log.read_text()
            (retro/"d35-launcher1/home-grid.rgb565").touch()
            events.unlink()
            invoke(board)
            assert "layout=grid\n" in log.read_text() and events.read_text()=="card\n"
        stop.unlink()
        invoke(card)
        assert not stop.exists() and events.read_text()=="card\nsupervisor\n"
        # No-card firmware branch still selects the built-in fallback.
        (retro/"init").unlink()
        events.unlink()
        invoke(board)
        assert events.read_text()=="fallback\n"
    print("PASS original BusyBox startup: old firmware, active splash refusal, firmware handoff, and no-card fallback")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared",type=Path)
    check(parser.parse_args().prepared)
