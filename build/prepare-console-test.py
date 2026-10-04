"""Prepare one-boot userspace-console suppression with the same passive observer."""
from pathlib import Path
base = Path(__file__).resolve().parent
source = (base / 'hardware-runtime-probe.c').read_text()
source = source.replace('\\\"version\\\":2', '\\\"version\\\":3')
source = source.replace('"/sys/kernel/irq/19/name", NULL', '"/sys/kernel/irq/19/name", "/sys/module/printk/parameters/ignore_loglevel", NULL')
source = source.replace('"/dev/chunkmem", "/dev/scale",', '"/proc/kcore", "/dev/chunkmem", "/dev/scale",')
(base / 'hardware-console-probe.c').write_text(source,newline='\n')
build = (base / 'build-hardware-runtime-probe.sh').read_text().replace('hardware-runtime-probe','hardware-console-probe')
(base / 'build-hardware-console-probe.sh').write_text(build,newline='\n')
verify = (base / 'verify-hardware-runtime-probe.py').read_text().replace('hardware-runtime-probe','hardware-console-probe').replace("['version'] == 2", "['version'] == 3")
(base / 'verify-hardware-console-probe.py').write_text(verify,newline='\n')
install = (base / 'install-hardware-runtime-probe.py').read_text().replace('Hardware-Runtime-v2','Hardware-Console-v3').replace('hardware_probe_v2','hardware_probe_v3').replace('hardware-runtime-probe','hardware-console-probe')
old = "candidate = original.replace(anchor, hook + anchor)\nassert candidate.replace(hook, b'') == original"
new = '''launch = b"  /usr/retro/main &\\n"
quiet = b"""  # One boot only: discard frontend userspace console output.
  if [ -f /usr/retro/hardware_probe_v3.once ]; then
    /usr/retro/main > /dev/null 2>&1 &
  else
    /usr/retro/main &
  fi
"""
assert original.count(launch) == 1
candidate = original.replace(launch, quiet).replace(anchor, hook + anchor)
assert candidate.replace(hook, b'').replace(quiet, launch) == original'''
assert old in install
install = install.replace(old,new)
(base / 'install-hardware-console-probe.py').write_text(install,newline='\n')
collect = (base / 'collect-hardware-runtime-probe.py').read_text().replace('Hardware-Runtime-v2','Hardware-Console-v3').replace('hardware_probe_v2','hardware_probe_v3').replace('hardware-runtime-return-','hardware-console-return-')
(base / 'collect-hardware-console-probe.py').write_text(collect,newline='\n')
print('Prepared console-output experiment; changes no kernel console setting')
