"""Analyze a retained PCM flight history; no device access or writes.

Accepted minus hardware count is an accounting comparison, not a certified
playable reserve after unexplained application-pointer changes. Rates use
matched WRITE_OK anchors, excluding the time spent persisting the fault.
"""
from pathlib import Path
import argparse,json,re,statistics

def analyze(path,rate):
    text=path.read_text(encoding='utf-8')
    rows=[]
    for line in text.splitlines():
        if line.startswith('seq='):
            row=dict(piece.split('=',1) for piece in line.split())
            rows.append({k:v if k=='op' else int(v) for k,v in row.items()})
    assert rows and all(b['seq']==a['seq']+1 for a,b in zip(rows,rows[1:]))
    assert len({r['epoch'] for r in rows})==1,'Analyze one epoch at a time'
    samples=[r for r in rows if r['op']=='SYNC_OK']
    changes=[];previous=None
    for r in samples:
        difference=r['appl']-r['xfer']
        if previous is not None and difference!=previous:
            changes.append({'seq':r['seq'],'kernel_ns':r['ns'],'delta_change':difference-previous,
                'appl_minus_accepted':difference,'state':r['state'],'reported_queued':r['queued'],
                'accepted_minus_reported_hw':r['xfer']-r['hw']})
        previous=difference
    # This workload publishes a large mixed batch followed by a small tail.
    # Do not generalize these anchors to arbitrary core batching schemes.
    anchors=[r for r in rows if r['op']=='WRITE_OK' and 650<=r['result']<=800]
    interval=None
    if len(anchors)>=3:
        a,b=anchors[0],anchors[-1];seconds=(b['ns']-a['ns'])/1e9
        intervals=[(y['ns']-x['ns'])/1e6 for x,y in zip(anchors,anchors[1:])]
        frames=b['xfer']-a['xfer']
        interval={'first_seq':a['seq'],'last_seq':b['seq'],'anchor_count':len(anchors),
            'elapsed_ms':seconds*1000,'accepted_frames':frames,
            'accepted_frames_per_second':frames/seconds,'negotiated_frames_per_second':rate,
            'production_shortfall_fraction':1-frames/(seconds*rate),
            'mean_large_batch_interval_ms':statistics.mean(intervals),
            'min_large_batch_interval_ms':min(intervals),'max_large_batch_interval_ms':max(intervals),
            'reported_hw_advance':b['hw']-a['hw'],
            'accepted_minus_hw_change':frames-(b['hw']-a['hw']),
            'limit':'Large-batch cadence is a workload-specific frame-production proxy, not a per-call CPU measurement.'}
    kernel=re.search(r'kernel_read_all_bytes=(-?\d+) errno=(\d+)',text)
    result={'trace_version':text.splitlines()[0],'retained_operations':len(rows),'epoch':rows[0]['epoch'],
        'accepted_pointer_difference_first_sample':samples[0]['appl']-samples[0]['xfer'],
        'application_pointer_difference_changes':changes,'matched_large_batch_interval':interval,
        'last_successful_observation':next(r for r in reversed(samples) if r['state']==3),
        'final_observation':samples[-1],
        'kernel_read_result':{'bytes':int(kernel[1]),'errno':int(kernel[2])} if kernel else None,
        'causal_limit':'Trace shows reserve erosion before pointer divergence. It does not identify who changes appl_ptr, padding contents, or which core subsystem costs time.'}
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('trace',type=Path)
    parser.add_argument('--rate',type=int,default=44100);args=parser.parse_args()
    print(json.dumps(analyze(args.trace,args.rate),indent=2))
