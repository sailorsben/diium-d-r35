"""Derive guarded release tools; new folder, archive, identity and authority."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def prepare():
    for kind in ('finalize','install','publish'):
        old=ROOT/f'build/{kind}-ability-regression.py'
        s=old.read_text().replace('ability-regression-private-v1','ability3-private-v1').replace('snes-ability2','snes-ability3').replace('ability2','ability3').replace('ability-regression','ability3')
        s=s.replace('Fix shared failure patterns and provide an automated subset of the largest set.','Evaluate returned I: test, fix supported bugs, and rearm a new test.')
        if kind=='finalize':
            s=s.replace("for d in ('runner','core')", "for d in ('runner','core','counted-core')")
            s=s.replace("'plus-a7-multi-window.h'", "'plus-a7-multi-window.h','plus-a7-math-palette.h','plus-a7-math-check.c','check-ability3-math.sh','prepare-ability3-release.py'")
            # Names after generic replacement must refer to actual authored tools.
            s=s.replace("'prepare-ability3.py'", "'prepare-ability3.py'")
            s=s.replace("proof+=list", "proof+=[OUT/'math-check.log',OUT/'qualify.py']\n    proof+=list")
        if kind=='publish':
            s=s.replace("summary['hardware_result']='PENDING'", "summary['hardware_result']='PENDING'\n    summary['independent_scalar_palette_checks']=2097152\n    summary['math_check_log_sha256']=digest(OUT/'math-check.log')")
            s=s.replace('Counter-free Mode1 multi-background/irrelevant Window2 batching; other core code unchanged.', 'Counter-free fixed-operand math-palette reuse atop ability2; original mixed/subscreen/clipped/direct-color paths retained.')
        (ROOT/f'build/{kind}-ability3.py').write_text(s,newline='\n')
if __name__=='__main__':prepare()
