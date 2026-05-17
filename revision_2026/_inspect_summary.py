import json
s = json.loads(open(r'd:\repo\ekyc\revision_2026\results\summary.json', encoding='utf-8').read())
for model, tiers in s.items():
    for tier_name in ('T0', 'T1', 'T4'):
        td = tiers.get(tier_name)
        if not td:
            continue
        acc = td['accuracy']['mean'] * 100
        cer = td['cer']['mean'] * 100
        wer = td['wer']['mean'] * 100
        p = td['precision']['mean'] * 100
        r = td['recall']['mean'] * 100
        f1 = td['f1']['mean'] * 100
        layout = td['layout']['mean'] * 100
        lat = td['latency_s']['mean']
        print(f'{model:20s} {tier_name}  acc={acc:6.2f}  CER={cer:6.2f}  WER={wer:6.2f}  P={p:6.2f}  R={r:6.2f}  F1={f1:6.2f}  layout={layout:6.2f}  lat={lat:7.3f}s')
    print()
