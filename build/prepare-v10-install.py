from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'install-v9-render.py').read_text()
s=s.replace('SNES-Plus-v9-core-render-test','SNES-Plus-v10-audio-priority').replace('v9-render','v10-budget')
s=s.replace('bin,render_off,','bin,adaptive_enabled,')
s=s.replace("assert sum(int(r['draws'])", "rows = [r for r in rows if r.get('calls') is not None]\nassert sum(int(r['calls']) for r in rows) == 4200\nassert sum(int(r['draws'])", 1)
s=s.replace("== 3000", "== 2100").replace("== 1200", "== 2100")
s=s.replace("assert all(int(r['draws']) == 0 for r in rows if r['render_off'] == '1')", "assert all(int(r['draws']) + int(r['duplicates']) == int(r['calls']) for r in rows)")
s=s.replace("'actual_core_video_frames':3000, 'duplicate_video_callbacks':1200", "'actual_core_video_frames':2100, 'duplicate_video_callbacks':2100")
s=s.replace("'hardware_result':'pending'", "'hardware_result':'pending', 'adaptive_budget_check':'697/2000 skips for measured mine costs; average 15355 us; light workload returns to full drawing'")
start=s.index("(package/'instructions.txt').write_text('''")
end=s.index("''')",start)+4
s=s[:start]+'''(package/'instructions.txt').write_text("""D-R35 v10: adaptive audio priority

Load the FF6 mine save and listen while standing still, then walk around.
Open and close FF6's party menu for comparison, then try a battle.
There is no timed picture hold. When frame work is too expensive, some frames
are not drawn; game CPU and audio keep running every frame. At most half of
drawing is skipped. Video can be less smooth in heavy scenes.

After about a minute on the map, ESC -> Save state to an unused slot if available
to write the report, then exit the game normally. Reconnect D: for collection.
Report: retro/emu_sfc_plus_v10_audio_priority.txt. No gameplay disk logging.
Existing Plus save states remain compatible; estimates restart on state load.
The rollback ZIP restores the exact clean adapter. The Plus core is unchanged.
Hardware results remain pending until you test this build.
""")'''+s[end:]
s=s.replace('v9tmp','v10tmp').replace('v9 core-render A/B','v10 adaptive audio priority')
(p/'install-v10-budget.py').write_text(s,newline='\n')
