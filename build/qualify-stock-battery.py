"""Qualify the exact SD frontend's ADC/warning path offline. Never opens I:."""
from pathlib import Path
from hashlib import sha256
import json, subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'device-evidence/battery-offline-review'
CARD = '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
DRIVER = 'd34ddc39546399759d374e60f4a523ddd5a388412ee6a94c9e95feddf4ab46d5'
CONFIG = '842e7cb861c6ce2faea7182f22236cb9ac26b34ac7f51e75f79702e47976343f'

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def run(args):
    return subprocess.check_output(['wsl', '--exec', *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT)

def main():
    assert digest(OUT/'card-vrtemu') == CARD
    assert digest(OUT/'gp_adc_module.ko') == DRIVER
    assert digest(OUT/'adcset.ini') == CONFIG
    assert (OUT/'adcset.ini').read_bytes() == b'318,310,300,290,275\r\n'
    # Independent pre-kernel inventory pins the same active SD program/config.
    prior = json.loads((ROOT/'device-evidence/uart-kernel-before-20261017T011353008133Z/archive.json').read_text())
    hashes = {e['path']:e['sha256'] for e in prior['all_retro_files']}
    assert hashes['retro/vrtemu'] == CARD and hashes['retro/adcset.ini'] == CONFIG
    compile_args = ['arm-linux-gnueabihf-gcc', '-mcpu=cortex-a7', '-marm', '-O2',
                    '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                    '-no-pie', '-Wl,-Ttext-segment=0x10000000',
                    'build/check-stock-adc-logic.c', '-o',
                    'device-evidence/battery-offline-review/check-stock-adc-logic']
    run(compile_args)
    execution = run(['qemu-arm', '-cpu', 'cortex-a7', '-L', '/usr/arm-linux-gnueabihf',
                     'device-evidence/battery-offline-review/check-stock-adc-logic',
                     'device-evidence/battery-offline-review/card-vrtemu'])
    assert '49152' in execution and 'Intercepted stock shutdown command: poweroff' in execution
    (OUT/'execution.txt').write_text(execution, encoding='utf-8')
    # Preserve exact vendor-function disassemblies privately, with relocation names.
    driver = b''
    for fn in ['gp_adc_request', 'gp_adc_fops_open', 'gp_adc_read', 'gp_adc_fops_read', 'gp_adc_fops_ioctl']:
        driver += run(['arm-linux-gnueabihf-objdump', '-dr', '--disassemble='+fn,
                       'device-evidence/battery-offline-review/gp_adc_module.ko']).encode()
    (OUT/'adc-driver-trace.txt').write_bytes(driver)
    assert b'str\tr1, [r3, #12]' in driver  # New handle saved value initialized to zero.
    assert b'add\tr4, r4, #32768' in driver  # Semaphore-timeout flag plus saved value.
    assert b'mov\tr2, #2' in driver         # Successful read copies two bytes.
    card_trace = ''
    for fn in ['xintiao', 'mui_WaitNMI', 'Load_Proc2', 'get_executable_path', 'gpio_read_ioc11']:
        card_trace += run(['arm-linux-gnueabihf-objdump', '-d', '--disassemble='+fn,
                          'device-evidence/battery-offline-review/card-vrtemu'])
    (OUT/'card-battery-trace.txt').write_text(card_trace, encoding='utf-8')
    report = {
        'offline_checks_passed': True, 'raw_state_GPIO_timeout_combinations': 49152,
        'card_frontend_sha256': CARD, 'adc_driver_sha256': DRIVER, 'card_config_sha256': CONFIG,
        'card_thresholds': [318,310,300,290,275], 'config_and_frontend_unchanged_since_before_kernel_flash': True,
        'adc_channel': 2, 'successful_driver_read_bytes': 2, 'frontend_requests_bytes': 4,
        'scale': 'floor((raw16 & 1023) * 330 / 1024)',
        'critical_scaled_at_or_below': 275, 'critical_raw10_at_or_below': 856,
        'driver_timeout_per_fresh_handle': 'saved_value=0; returned uint16=0x8000; frontend masks to zero',
        'false_low_reproduced': 'failed read after zero sample classified critical; exact stock ARM code',
        'negative_state_blocks_heartbeat_resampling': True,
        'external_state_override': 'GPIO 0x20b and 0x20e both nonzero -> level 5; pin electrical meaning unverified',
        'menu_critical_path_executed': 'warning.zip/poweroff.raw -> display -> sleep(5) -> backlight off -> intercepted poweroff',
        'physical_timeout_or_read_failure_observed': False,
        'physical_battery_voltage_capacity_or_charging_proven': False,
        'root_cause': 'UNRESOLVED: concrete false-low mechanism, missing runtime ADC returns/flags/GPIO',
        'sources': {n:digest(ROOT/n) for n in ['build/check-stock-adc-logic.c','build/qualify-stock-battery.py']},
        'execution_sha256': digest(OUT/'execution.txt'),
        'no_card_access': True, 'no_flash': True, 'no_full_backup': True,
    }
    (OUT/'qualification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    public = ROOT/'evidence/2026-10-16/stock-battery-trace'
    public.mkdir(parents=True, exist_ok=True)
    for name in ['qualification.json','execution.txt']:
        (public/name).write_bytes((OUT/name).read_bytes())
    print(execution)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
