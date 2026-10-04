"""Decode the passive report; retain numeric samples and evidence boundaries."""
import collections
import json
from pathlib import Path
import re
import struct
import sys

out = Path(sys.argv[1])
report = next(p for p in [out / 'hardware_probe_v1.jsonl', out / 'hardware_probe_v2.jsonl', out / 'hardware_probe_v3.jsonl'] if p.exists())
records = [json.loads(line) for line in report.read_text().splitlines()]
files = collections.defaultdict(list)
for r in records:
    if r['kind'] == 'file': files[r['path']].append(r)
tick = records[0]['clk_tck']
def first(path):
    r = files[path][0]
    assert r['errno'] == 0 and not r['truncated'], path
    return bytes.fromhex(r['data']) if r['encoding'] == 'hex' else r['data'].encode('latin1')

dtb = first('/sys/firmware/fdt')
(out / 'device-tree.dtb').write_bytes(dtb)
magic, size, off_struct, off_strings, off_reserve, version, lastversion, bootcpu, sz_strings, sz_struct = struct.unpack_from('>10I', dtb)
assert magic == 0xd00dfeed and size == len(dtb)
names = dtb[off_strings:off_strings + sz_strings]
props = {}
stack = []
offset = off_struct
while offset < off_struct + sz_struct:
    token, = struct.unpack_from('>I', dtb, offset); offset += 4
    if token == 1:
        end = dtb.index(0, offset)
        stack.append(dtb[offset:end].decode())
        offset = (end + 4) & ~3
    elif token == 2: stack.pop()
    elif token == 3:
        n, nameoff = struct.unpack_from('>II', dtb, offset); offset += 8
        name = names[nameoff:names.index(0, nameoff)].decode()
        data = dtb[offset:offset+n]; offset = (offset + n + 3) & ~3
        node = '/' + '/'.join(x for x in stack if x)
        if data and any(32 <= b <= 126 for b in data) and data[-1] == 0 and all(b == 0 or 32 <= b <= 126 for b in data):
            decoded = data.rstrip(b'\0').decode().split('\0')
        elif n and n % 4 == 0:
            decoded = [hex(x) for x in struct.unpack('>' + 'I' * (n // 4), data)]
        else: decoded = data.hex()
        props.setdefault(node, {})[name] = {'hex': data.hex(), 'decoded': decoded}
    elif token == 4: pass
    elif token == 9: break
    else: raise ValueError((offset, token))
(out / 'device-tree.json').write_text(json.dumps(props, indent=2) + '\n')

def stat(r):
    text = r['data']; start = text.index('('); end = text.rindex(')')
    fields = text[end+1:].split()
    def field(n): return fields[n-3]
    return {'elapsed': r['elapsed'], 'tid': int(text[:start]), 'name': text[start+1:end],
            'state': field(3), 'utime': int(field(14)), 'stime': int(field(15)),
            'priority': int(field(18)), 'nice': int(field(19)), 'starttime': int(field(22)),
            'processor': int(field(39)), 'rt_priority': int(field(40)), 'policy': int(field(41))}
threads = {}
for path, rr in files.items():
    if not re.fullmatch(r'/proc/\d+/task/\d+/stat', path): continue
    series = [stat(r) for r in rr if r['errno'] == 0]
    a, b = series[0], series[-1]
    assert a['starttime'] == b['starttime'] and len(series) == 45
    seconds = b['elapsed'] - a['elapsed']
    intervals = []
    for prev, cur in zip(series, series[1:]):
        dt = cur['elapsed'] - prev['elapsed']
        intervals.append({'end_elapsed': cur['elapsed'], 'seconds': dt,
                          'user_cpu_percent': 100 * (cur['utime']-prev['utime'])/tick/dt,
                          'kernel_cpu_percent': 100 * (cur['stime']-prev['stime'])/tick/dt})
    threads[path] = {'first': a, 'last': b, 'seconds': seconds,
                     'user_cpu_percent': 100 * (b['utime']-a['utime'])/tick/seconds,
                     'kernel_cpu_percent': 100 * (b['stime']-a['stime'])/tick/seconds,
                     'wchan': [r['data'] for r in files[path[:-4] + 'wchan']], 'intervals': intervals}

cpu = []
for r in files['/proc/stat']:
    cpu.append({'elapsed': r['elapsed'], 'ticks': [int(x) for x in r['data'].splitlines()[0].split()[1:]]})
a, b = cpu[0], cpu[-1]
deltas = [y-x for x,y in zip(a['ticks'], b['ticks'])]
labels = ['user','nice','system','idle','iowait','irq','softirq','steal','guest','guest_nice']
total = sum(deltas[:8])
global_cpu = {k: 100 * v/total for k,v in zip(labels, deltas)}

def irqs(r):
    result = {}
    for line in r['data'].splitlines():
        m = re.match(r'\s*(\d+):\s+(\d+)\s+(.*)', line)
        if m: result[m[1]] = {'count': int(m[2]), 'label': m[3]}
    return result
sampled_irqs = [r for r in files['/proc/interrupts'] if r['elapsed'] > 14]
irq0, irq1 = sampled_irqs[0], sampled_irqs[-1]
assert irq0['elapsed'] > 14
prev, cur = irqs(irq0), irqs(irq1)
seconds = irq1['elapsed'] - irq0['elapsed']
irq_rates = {k: {'label': v['label'], 'delta': v['count'] - prev[k]['count'],
                 'per_second': (v['count'] - prev[k]['count'])/seconds} for k,v in cur.items()}
mem = []
for r in files['/proc/meminfo']:
    values = {k: int(v) for k,v in re.findall(r'^(\w+):\s+(\d+)', r['data'], re.M)}
    mem.append({'elapsed': r['elapsed'], **{k: values[k] for k in ['MemAvailable','MemFree','SwapTotal','SwapFree']}})
result = {'record_count': len(records), 'complete': records[-1], 'global_cpu_percent': global_cpu,
          'global_interval_seconds': b['elapsed'] - a['elapsed'], 'threads': threads,
          'global_accounted_cpu_seconds': total/tick,
          'global_cpu_accounting_note': 'Percentages normalized to reported ticks. Ticks do not cover the entire wall interval; do not treat as an exact utilization or interrupt-time measurement.',
          'interrupts': irq_rates, 'memory': mem,
          'device_tree_clock_hz': int.from_bytes(first('/proc/device-tree/cpus/cpu@0/clock-frequency'), 'big'),
          'perf_capabilities': [r for r in records if r['kind'] == 'perf_capability'],
          'unavailable_paths': {k: rr[0]['errno'] for k,rr in files.items() if rr[0]['errno']},
          'truncated_paths': [k for k,rr in files.items() if any(r['truncated'] for r in rr)]}
tty_rows = files.get('/proc/tty/driver/gp serial', [])
if tty_rows:
    tty_rows = [r for r in tty_rows if r['elapsed'] > 14]
    def tty_counts(r):
        line = next(line for line in r['data'].splitlines() if line.startswith('0:'))
        return {k:int(v) for k,v in re.findall(r'(irq|tx|rx|brk):(\d+)',line)}
    ta, tb = tty_rows[0], tty_rows[-1]
    ca, cb = tty_counts(ta), tty_counts(tb)
    duration = tb['elapsed'] - ta['elapsed']
    result['uart0'] = {'seconds': duration, 'first': ca, 'last': cb,
        'per_second': {k:(cb[k]-ca[k])/duration for k in ['tx','rx','brk']},
        'note': 'Reported serial counters need not include polling console output. They are not a UART hardware trace.'}
result['kernel_symbol_records'] = [{k:v for k,v in r.items() if k != 'data'} for r in records if r['kind'] == 'kernel_symbols']
result['kernel_log_records'] = []
for r in records:
    if r['kind'] != 'kernel_log': continue
    log_times = [float(x) for x in re.findall(r'^(?:<\d+>)?\[\s*([\d.]+)\]', r['data'], re.M)]
    result['kernel_log_records'].append({k:v for k,v in r.items() if k != 'data'} | {
        'chars':len(r['data']), 'lines':len(r['data'].splitlines()),
        'first_timestamp':log_times[0] if log_times else None,
        'last_timestamp':log_times[-1] if log_times else None,
        'message_counts':dict(collections.Counter(re.sub(r'^<\d+>\[.*?\] ','',line) for line in r['data'].splitlines()))})
(out / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
print('CPU', global_cpu)
for path, v in threads.items():
    print(path, 'user', round(v['user_cpu_percent'],3), 'kernel', round(v['kernel_cpu_percent'],3), 'wchan',v['wchan'])
    print('interval CPU totals', [round(x['user_cpu_percent'] + x['kernel_cpu_percent'],1) for x in v['intervals']])
print('IRQs',json.dumps(irq_rates, indent=2))
print('DT hardware nodes')
for path, fields in props.items():
    if 'interrupts' in fields or 'clock-frequency' in fields or any(x in path.lower() for x in ['gpu','pmu','cache','pscale','dac','memory']):
        print(path, json.dumps(fields))
print('truncated',result['truncated_paths'])
