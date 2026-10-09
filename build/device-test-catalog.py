"""List current executable survey/lab tests and explicit evidence boundaries."""
import argparse,json
CATALOG=[
 {'id':'identity','mode':'passive','owner':'device-survey-1','question':'What kernel, CPU, RAM, boot arguments and mount roots actually run?'},
 {'id':'boot-tools','mode':'passive','owner':'device-survey-1','question':'What do startup, power, watchdog and NAND helper binaries really implement?'},
 {'id':'firmware-storage','mode':'passive','owner':'device-survey-1','question':'Which block/MTD/SPI devices and driver/DT identities are exposed?'},
 {'id':'usb','mode':'passive','owner':'device-survey-1','question':'Is a UDC registered, a gadget configured, or any USB function/device exposed?'},
 {'id':'devices-processes','mode':'passive','owner':'device-survey-1','question':'Who holds display, PCM, input and other device handles; which interfaces exist?'},
 {'id':'power-clocks','mode':'passive','owner':'device-survey-1','question':'Which cpufreq, thermal, battery and hwmon measurements exist?'},
 {'id':'module-runtime-inventory','mode':'passive','owner':'device-survey-1','question':'Which tools/libraries/module files are present and what does offline ELF analysis reveal?'},
 {'id':'device-tree','mode':'passive','owner':'device-survey-1','question':'Which buses, peripherals, memory reservations and compatibility strings are declared?'},
 {'id':'final-sample','mode':'passive','owner':'device-survey-1','question':'How did uptime, memory, CPU and interrupt counts change during this diagnostic run?'},
 {'id':'cpu-neon-memory','mode':'active-existing','owner':'platform-lab-1/2','question':'Compare scalar/NEON kernels, memory/cache work and known workload costs.'},
 {'id':'timing-readiness','mode':'active-existing','owner':'platform-lab-2','question':'Measure kernel-clock deadlines, relative waits and PCM-driven readiness.'},
 {'id':'display-scaler','mode':'active-existing','owner':'platform-lab-1/2','question':'Qualify exact scaler completion/release, buffer ownership and visual output.'},
 {'id':'pcm-continuity','mode':'active-existing','owner':'snes-mvp-1.18 and platform-lab-2','question':'Locate native PCM starvation/state/pointer failures with exact owner diagnostics.'},
 {'id':'input-mapping','mode':'active-existing','owner':'snes-mvp input references','question':'Qualify physical controls through the independent stock libretro mask table.'},
 {'id':'persistence','mode':'active-controlled','owner':'current save/flush contracts','question':'Verify graceful exit and safe card return without deliberately corrupting FAT.'},
 {'id':'recovery-usb','mode':'discovery-required','owner':'boot ROM/bootloader unknown','question':'Identify an actual recovery mode and VID/PID before trying a documented sequence.'},
 {'id':'flash-readback','mode':'discovery-required','owner':'NAND/SPI identity unknown','question':'Identify storage protocol and obtain verified private readback before modifying firmware.'},
 {'id':'persistent-splash','mode':'discovery-required','owner':'internal /showlogo','question':'Repack a verified persistent boot image and establish matching recovery before replacement.'},
 {'id':'gpu-dma','mode':'discovery-required','owner':'vendor runtime unknown','question':'Find a usable GPU/DMA API and memory/lifetime contract before executing jobs.'},
]
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',action='store_true');a=p.parse_args()
 if a.json:print(json.dumps(CATALOG,indent=2))
 else:
  for t in CATALOG:print(f"{t['id']:25} {t['mode']:20} {t['question']}")
