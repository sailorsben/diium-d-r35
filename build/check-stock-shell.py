"""Run paired ARM/QEMU stock-shell checks on locally supplied replay fixtures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
from statistics import median
import subprocess


ROOT = Path(__file__).resolve().parent.parent
ADAPTER = "3a0ceb3cfde5148cecec0fb7cf5cf4c57229f9c6040626f79de3a520ae38c00e"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("output", "stock", "adapter", "fixtures"):
        parser.add_argument(arg, type=lambda s: Path(s).resolve())
    parser.add_argument("--pairs", type=int, default=2)
    args = parser.parse_args()
    out = args.output
    assert sha256(args.adapter.read_bytes()).hexdigest() == ADAPTER
    z = ROOT / "build/sysroot/lib/libz.so.1"
    runtime = out / "test-libs"
    runtime.mkdir(exist_ok=True)
    if not (runtime / z.name).exists():
        (runtime / z.name).symlink_to(z)
    test = out / "check"
    subprocess.run(["arm-linux-gnueabihf-gcc", "-Wall", "-Wextra", "-Werror", "-std=gnu11", "-O2",
                    "-mcpu=cortex-a7", "-marm", "-fPIE", "-pie", "-DUSE_BLARGG_APU",
                    "-Ibuild/snes9x2005/libretro-common/include", "build/check-stock-shell.c",
                    "-Lbuild/sysroot/lib", "-l:libz.so.1", "-ldl", "-o", str(test)], cwd=ROOT, check=True)
    stock, direct = args.stock, out / "vrtemu"
    core = out / "libs/d35-snes.so"
    other_core=out/"paired-core.so"
    if not other_core.exists():
        other_core.write_bytes(core.read_bytes())
    cpus = sorted(os.sched_getaffinity(0))
    lanes = list(dict((Path(f"/sys/devices/system/cpu/cpu{i}/topology/thread_siblings_list").read_text(), i)
                      for i in cpus).values())

    def call(game, mode, lane, run_dir, check="verify", ticks=1200):
        run_dir.mkdir(exist_ok=True)
        env = ["-E", f"LD_LIBRARY_PATH={runtime}", "-E", f"D35_PAIR_CORE={other_core}"]
        cmd = ["taskset", "-c", str(lane), "qemu-arm", "-cpu", "cortex-a7", "-L", "/usr/arm-linux-gnueabihf",
               *env, str(test), str(stock if mode=="stock" else direct), str(core),
               str(args.fixtures/f"{game:03}"), str(args.adapter), mode, check, str(ticks)]
        result = subprocess.run(cmd, cwd=run_dir, text=True, capture_output=True, timeout=240)
        if result.returncode:
            raise RuntimeError(f"{game}/{mode} {result.returncode}: {result.stdout} {result.stderr}")
        row = next(s for s in result.stdout.splitlines() if s.startswith("mode="))
        return {k: int(v) if k.endswith("_ns") or k in ("pictures", "ticks", "pcm_frames") else v
                for k, v in (piece.split("=") for piece in row.split())}

    def replay(game):
        lane = lanes[game % len(lanes)]
        work = out / f"fixture-{game}"
        results = {mode: call(game, mode, lane, work) for mode in ("stock", "direct", "auto")}
        ref, candidate, auto = (results[m] for m in ("stock", "direct", "auto"))
        for field in ("video", "pcm", "layout", "pcm_frames", "state"):
            assert ref[field] == candidate[field], (game, field, results)
        for field in ("pcm", "layout", "pcm_frames", "state"):
            assert candidate[field] == auto[field], (game, field, results)
        assert auto["pictures"] <= candidate["pictures"] <= ref["pictures"]
        pairs = []
        for i in range(args.pairs):
            order = ("stock", "direct") if not i%2 else ("direct", "stock")
            pairs.append({m: call(game, m, lane, work, "timing") for m in order})
        for key in ("launch_ns", "game_ns"):
            results[f"paired_{key}_delta"] = median(p["stock"][key]-p["direct"][key] for p in pairs) if pairs else None
        results["pairs"] = pairs
        results["inprocess_pairs"]=[call(game,"paired",lane,work,"timing") for _ in range(args.pairs)]
        print(f"game {game}: {ref['pictures']} stock submits, {candidate['pictures']} direct, {auto['pictures']} auto; PCM exact", flush=True)
        return results

    with ThreadPoolExecutor(max_workers=min(5,len(lanes))) as pool:
        games = list(pool.map(replay, range(5)))
    zip_case = call(0, "zip", lanes[0], out/"fixture-zip", ticks=120)
    raw_case = call(0, "direct", lanes[0], out/"fixture-raw", ticks=120)
    for field in ("video", "pcm", "layout", "pcm_frames", "state"):
        assert zip_case[field] == raw_case[field]
    reject_case = call(0, "reject", lanes[0], out/"fixture-reject", ticks=1)
    assert reject_case["ticks"] == 0
    report = {"physical": False, "games": games, "zip": zip_case, "raw": raw_case, "reject": reject_case}
    (out/"qualification.json").write_text(json.dumps(report, indent=2)+"\n")


if __name__ == "__main__":
    main()
