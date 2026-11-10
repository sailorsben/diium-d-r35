"""Aggregate the matched physical baseline and local throughput experiments."""
import csv
import hashlib
import json
from pathlib import Path
import re
from statistics import mean, median
import struct
import sys


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def kv(p):
    return dict(line.split('=', 1) for line in p.read_text().splitlines() if '=' in line)


def quantile(data, p):
    return sorted(data)[(len(data)-1)*p//100]


def elf_text(path):
    """Read ELF32 section bytes without writing or remapping the core file."""
    data=path.read_bytes()
    assert data[:6]==b'\x7fELF\x01\x01'
    offset,=struct.unpack_from('<I',data,32)
    width,count,strings=struct.unpack_from('<HHH',data,46)
    sections=[struct.unpack_from('<10I',data,offset+i*width) for i in range(count)]
    names=sections[strings][4]
    section,=[s for s in sections if data[names+s[0]:].split(b'\0',1)[0]==b'.text']
    return hashlib.sha256(data[section[4]:section[4]+section[5]]).hexdigest()


def physical(archive):
    result, = (archive/'retro/snes-fivegame-kernel2/results').glob('run-*')
    prior = json.loads((archive/'fivegame-replay-analysis.json').read_text())
    out = []
    for e in prior['epochs']:
        d = result / f"run-{e['run']:03}"
        p = d/'frames.csv'
        with p.open() as f:
            rows = [{k:int(v) for k,v in row.items()} for row in csv.DictReader(x for x in f if not x.startswith('#'))]
        head = kv(d/'headroom.txt')
        assert head['physical']=='1' and len(rows)==e['rendered']==int(head['rows'])
        valid = []
        for row in rows:
            if not row['pointer_valid']: break
            valid.append(row)
        period = int(head['period_ns'])
        record = dict(run=e['run'],game=e['fixture'],policy=e['policy'],period_ns=period,
                      valid_prefix=len(valid),rendered=len(rows),skipped=e['skipped'],
                      sources={x:sha(d/x) for x in ['frames.csv','headroom.txt','pcm-full.txt']})
        if e['fixture']==3:
            assert len(valid)==3 and len(rows)==4
            pcm = (d/'pcm-full.txt').read_text()
            matches = [dict(re.findall(r'(\w+)=([^ ]+)', line)) for line in pcm.splitlines() if line.startswith('seq=')]
            start, = [r for r in matches if r['op']=='SYNC_OK' and r['state']=='3' and r['hw']=='0' and r['arg']=='6']
            good = [r for r in matches if r['op']=='SYNC_OK' and r['state']=='3' and int(r['seq'])>=int(start['seq'])]
            assert all(int(r['appl'])==int(r['xfer']) for r in good)
            final, = [r for r in matches if r['op']=='SYNC_OBSERVE']
            need=lambda r: int(r['hw'])-int(r['xfer'])
            record.update(core_cpu_ns=[r['cpu_ns'] for r in valid], failed_frame_core_interval_cpu_ns=rows[-1]['cpu_ns'],
                          first_valid_prefix_core_cpu_mean_ns=round(mean(r['cpu_ns'] for r in valid)),
                          first_valid_prefix_core_only_excess_ns=round(mean(r['cpu_ns'] for r in valid)-period),
                          min_valid_reserve=min(-need(r) for r in good),
                          max_valid_drawdown_from_start=max(need(r)-need(start) for r in good),
                          nominal_final_deficit_frames=round((int(final['ns'])-int(start['ns']))*44100/1e9-(int(final['xfer'])-int(start['xfer'])),1),
                          final_accepted_minus_hw=int(final['xfer'])-int(final['hw']),
                          final_unexplained_appl_advance=int(final['appl'])-int(final['xfer']))
        else:
            assert e['status']=='CLEAN_BOUNDED_WINDOW' and len(valid)==1200
            w = rows[120:]
            a = int(head['final_audio_worker_CPU_ns']); v = int(head['final_video_worker_CPU_ns'])
            record.update(service_mean_ns=int(head['service_mean_ns']),service_p95_ns=int(head['service_p95_ns']),
                          service_p99_ns=int(head['service_p99_ns']),service_max_ns=int(head['service_max_ns']),
                          target_p95_gap_ns=int(head['service_p95_ns'])-(period*4//5),
                          min_valid_reserve=e['minimum_valid_sampled_reserve_frames'],
                          main_step_mean_ns=round(mean(r['main_step_cpu_ns'] for r in w)),
                          audio_worker_cpu_ns_per_call=round(a/len(rows)),video_worker_cpu_ns_per_call=round(v/len(rows)),
                          copied_bytes=rows[-1]['copied_payload_bytes'],direct_submitted=rows[-1]['direct_submitted'])
        out.append(record)
    return out


def replay(directory):
    meta = json.loads((directory/'manifest.json').read_text())
    out = []
    for row in meta['results']:
        p = directory/('{rep}-{core}-{game}-{mode}.log'.format(**row))
        log = p.read_text()
        m = re.search(r'cold_cpu_ns=(\d+) cold_calls=(\d+)',log)
        end = re.search(r'published=(\d+) audio_frames=(\d+) verified=(\d+) mismatched=(\d+) first_mismatch=(\d+)',log)
        assert m and end, p
        ns, calls = map(int,m.groups())
        rendered, audio, verified, mismatch, first = map(int,end.groups())
        data = [int(t) for t in re.findall(r'^\d+,([0-9]+)$',log,re.M)]
        assert len(data)==1200 and row['returncode']==(3 if mismatch else 0)
        warm = data[120:]
        rec = dict(**row, cold_cpu_ns=ns,cold_calls=calls,game_cpu_mean_ns=round(mean(warm)),
                   game_cpu_p95_ns=quantile(warm,95),game_cpu_first_four_ns=data[:4],
                   rendered=rendered,audio_frames=audio,verified=verified,mismatch=mismatch,first_mismatch=first,log_sha256=sha(p))
        if row['core']=='census':
            ops = [(int(n,16),int(c)) for n,c in re.findall(r'^opcode ([0-9a-f]+) (\d+)$',log,re.M)]
            fx = re.search(r'game_gsu ns=(\d+) runs=(\d+)',log)
            assert fx and ops
            gsu_ns, runs=map(int,fx.groups())
            rec.update(gsu_instrumented_ns=gsu_ns,gsu_instrumented_run_share=gsu_ns/sum(data),gsu_runs=runs,gsu_ops=sum(n for _,n in ops),
                       gsu_plot_ops=sum(n for op,n in ops if op in (0x04c,0x24c)),top_gsu_ops=sorted(ops,key=lambda x:-x[1])[:25])
        dma = re.search(r'game_dma spans=(\d+) bytes=(\d+) same=(\d+) same_bytes=(\d+)',log)
        if dma:
            rec['dma_census']=dict(zip(('spans','bytes','equal_spans','equal_bytes'),map(int,dma.groups())))
        key = re.search(r'reuse_key eligible=(\d+) hits=(\d+) false=(\d+)',log)
        if key:
            rec['reuse_key']=dict(zip(('eligible','hits','false_hits'),map(int,key.groups())))
        span = re.search(r'span_key calls=(\d+) eligible=(\d+) rows=(\d+) hits=(\d+) hit_rows=(\d+) modes=(\d+) complete=(\d+) false=(\d+)',log)
        if span:
            rec['span_key']=dict(zip(('calls','eligible','rows','hits','hit_rows','modes','complete','false_hits'),map(int,span.groups())))
        offset = re.search(r'offset_rows calls=(\d+) full=(\d+)',log)
        if offset:
            keys=('scanline_layers','no_offsets') if row['core']=='offset-plain-census' else ('tile_rows','full_width')
            rec['offset_rows']=dict(zip(keys,map(int,offset.groups())))
        out.append(rec)
    return dict(meta=meta,results=out)


def changes(result):
    rows = result['results']
    out = []
    for core,game,mode in sorted({(r['core'],r['game'],r['mode']) for r in rows}):
        if core=='baseline' or core=='physical' and mode=='full': continue
        r = [x for x in rows if (x['core'],x['game'],x['mode'])==(core,game,mode)]
        ref = {x['rep']:x for x in rows if (x['core'],x['game'],x['mode'])==('physical' if core=='physical' else 'baseline',game,'cold-off' if core in ('hot','dma-same','dma-delta') and game==3 else 'full')}
        record = dict(core=core,game=game,mode=mode)
        for key in ['game_cpu_mean_ns','game_cpu_p95_ns']+(['cold_cpu_ns'] if game==3 else []):
            x = [(1-a[key]/ref[a['rep']][key])*100 for a in r]
            record[key+'_saving_pct'] = dict(median=round(median(x),2),min=round(min(x),2),max=round(max(x),2))
        out.append(record)
    return out


def paired(directory):
    meta=json.loads((directory/'manifest.json').read_text())
    out=[]
    for row in meta['results']:
        p=directory/row['log']
        assert sha(p)==row['sha256']
        lines=p.read_text().splitlines()
        assert len(lines)==1203
        label,a,b=lines[0].split(',');assert label=='cold'
        work=[tuple(map(int,line.split(','))) for line in lines[1:1201]]
        assert [r[0] for r in work]==list(range(1200))
        base=[r[1] for r in work[120:]]; candidate=[r[2] for r in work[120:]]
        label,*frames=lines[-2].split(',');assert label=='published'
        label,*audio=lines[-1].split(',');assert label=='audio' and audio[0]==audio[1]
        def savings(x,y):return round(100*(1-y/x),2)
        out.append(dict(**row, cold_cpu_ns=[int(a),int(b)], cold_saving_pct=savings(int(a),int(b)) if row['game']==3 else None,
                        warm_cpu_mean_ns=[round(mean(base)),round(mean(candidate))],mean_saving_pct=savings(mean(base),mean(candidate)),
                        warm_cpu_p95_ns=[quantile(base,95),quantile(candidate,95)],p95_saving_pct=savings(quantile(base,95),quantile(candidate,95)),
                        warm_quarter_saving_pct=[savings(sum(base[i:i+270]),sum(candidate[i:i+270])) for i in range(0,1080,270)],
                        first_four_cpu_ns=[[r[1],r[2]] for r in work[:4]],rendered=list(map(int,frames)),audio_frames=int(audio[0])))
    return dict(meta=meta,results=out)


if __name__=='__main__':
    archive,out,followup,key,span,pair,offset,offset_pair,plain,plain_pair,plain_repeat,report=map(Path,sys.argv[1:])
    p=physical(archive)
    verify = replay(out/'verify')
    timing = replay(out/'timing')
    followup_verify=replay(followup/'followup-verify')
    followup_timing=replay(followup/'followup-timing')
    key_verify=replay(key/'reuse-verify')
    span_verify=replay(span/'span-verify')
    offset_verify=replay(offset/'offset-verify')
    plain_verify=replay(plain/'plain-verify')
    assert all(r['verified']==1200 and not r['mismatch'] for batch in
               (verify,followup_verify,key_verify,span_verify,offset_verify,plain_verify) for r in batch['results'])
    installed=Path(__file__).resolve().parent/'fivegame-kernel-private-v2/plus-a7.so'
    text_hash=elf_text(installed)
    assert all(elf_text(d/'baseline/snes9x2005_plus_libretro.so')==text_hash for d in (out,followup))
    report.write_text(json.dumps(dict(physical_baseline=p,offline_verify=verify,offline_timing=timing,
                                      offline_changes=changes(timing),followup_verify=followup_verify,
                                      followup_timing=followup_timing,followup_changes=changes(followup_timing),
                                      reuse_key_verify=key_verify,span_key_verify=span_verify,baseline_matching_ELF_text_sha256=text_hash,
                                      paired_offline_timing=paired(pair),offset_rows_verify=offset_verify,offset_rows_timing=paired(offset_pair),
                                      offset_plain_verify=plain_verify,offset_plain_timing=paired(plain_pair),
                                      offset_plain_timing_repeat=paired(plain_repeat),
                                      card_access=False),indent=2)+'\n')
