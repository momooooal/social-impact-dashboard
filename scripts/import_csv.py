#!/usr/bin/env python3
"""Import normalized CSV data as a fallback when an API is not yet available.

This intentionally uses a stable, cross-platform CSV schema rather than guessing every Meta
Business Suite export format. You can paste/export platform data into the provided templates.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'analytics.json'
NUM_FIELDS={'views','reach','profile_views','interactions','likes','comments','replies','shares','saves','reposts','quotes','clicks','follows','unfollows','followers','video_views','video_view_time'}

def read_json(p,default):
    if not p.exists():return default
    return json.loads(p.read_text(encoding='utf-8'))
def num(v):
    if v in (None,''):return None
    try:return float(str(v).replace(',',''))
    except ValueError:return None

def read_csv(path):
    if not path:return []
    with open(path,'r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--daily');ap.add_argument('--posts');ap.add_argument('--output',default=str(OUT));args=ap.parse_args()
    if not args.daily and not args.posts:ap.error('Provide --daily and/or --posts')
    out=Path(args.output);data=read_json(out,{'meta':{},'accounts':[],'daily':[],'posts':[],'warnings':[],'collection_log':[]})
    # Do not merge manual real-world data into the bundled demonstration dataset.
    if data.get('meta',{}).get('source')=='demo':
        project=data.get('meta',{}).get('project',{})
        data={'meta':{'project':project},'accounts':[],'daily':[],'posts':[],'warnings':[],'collection_log':[]}
    daily=read_csv(args.daily);posts=read_csv(args.posts)
    for rows in (daily,posts):
        for r in rows:
            for k in list(r):
                if k in NUM_FIELDS:
                    v=num(r[k]);
                    if v is None:r.pop(k,None)
                    else:r[k]=v
    dm={(r.get('date'),r.get('platform'),r.get('account_key')):r for r in data.get('daily',[])}
    for r in daily:
        if not all(r.get(k) for k in ('date','platform','account_key')):continue
        key=(r['date'],r['platform'],r['account_key']);dm[key]={**dm.get(key,{}),**r}
    pm={(r.get('platform'),r.get('account_key'),r.get('id')):r for r in data.get('posts',[])}
    for r in posts:
        if not all(r.get(k) for k in ('platform','account_key','id','timestamp')):continue
        key=(r['platform'],r['account_key'],r['id']);pm[key]={**pm.get(key,{}),**r}
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    data['daily']=sorted(dm.values(),key=lambda r:(r.get('date',''),r.get('platform',''),r.get('account_key','')))
    data['posts']=sorted(pm.values(),key=lambda r:r.get('timestamp',''),reverse=True)
    data.setdefault('meta',{})['generated_at']=now;data['meta']['source']='mixed/manual-import'
    data.setdefault('collection_log',[]).append({'time':now,'accounts_ok':0,'daily_rows':len(daily),'posts':len(posts),'warnings':0,'source':'manual-csv'})
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Imported daily={len(daily)} posts={len(posts)} -> {out}')
if __name__=='__main__':main()
