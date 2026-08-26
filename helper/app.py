from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from collector_core import (
    PLATFORMS, TOPICS, activity_catalog, app_data_dir, collect_all, config_path, current_setup_url, git_sync,
    import_content_file, import_private_messages, install_task, load_config, load_private_rows,
    remove_task, save_config, save_private_rows
)

LABELS = {'facebook':'Facebook','instagram':'Instagram','threads':'Threads'}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('社群資料小助手｜高雄市政府運動發展局')
        self.geometry('980x720')
        self.minsize(900,650)
        self.cfg = load_config()
        self.url_vars = {p: tk.StringVar(value=self.cfg['platforms'][p].get('insights_url','')) for p in PLATFORMS}
        self.repo_var = tk.StringVar(value=self.cfg.get('dashboard_repo_path',''))
        self.time_var = tk.StringVar(value=self.cfg.get('daily_time','18:00'))
        self.git_var = tk.BooleanVar(value=bool(self.cfg.get('auto_git_sync',False)))
        self.own_names_var = tk.StringVar(value=', '.join(self.cfg.get('own_sender_names',[])))
        self.status_var = tk.StringVar(value='準備完成。第一次使用請先完成三平台登入與頁面設定。')
        self.private_path = None
        self.private_rows = []
        self.private_activity_map = {'未歸類':''}
        self.private_topic_map = {v[0]:k for k,v in TOPICS.items()}
        self._build()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def _build(self):
        outer=ttk.Frame(self,padding=16); outer.pack(fill='both',expand=True)
        title=ttk.Label(outer,text='社群資料小助手',font=('Microsoft JhengHei UI',20,'bold')); title.pack(anchor='w')
        ttk.Label(outer,text='不保存帳號密碼；使用專用瀏覽器登入狀態，每日擷取彙總數據。私訊原文只在本機分析。').pack(anchor='w',pady=(2,12))
        nb=ttk.Notebook(outer); nb.pack(fill='both',expand=True)
        self.tab_setup=ttk.Frame(nb,padding=14); self.tab_import=ttk.Frame(nb,padding=14); self.tab_status=ttk.Frame(nb,padding=14)
        nb.add(self.tab_setup,text='① 首次設定'); nb.add(self.tab_import,text='② 月度匯入／私訊'); nb.add(self.tab_status,text='③ 執行與狀態')
        self._build_setup(); self._build_import(); self._build_status()
        bar=ttk.Frame(outer); bar.pack(fill='x',pady=(10,0)); ttk.Label(bar,textvariable=self.status_var).pack(side='left')

    def _build_setup(self):
        ttk.Label(self.tab_setup,text='A. 設定三平台登入與 Insights 頁面',font=('Microsoft JhengHei UI',13,'bold')).grid(row=0,column=0,columnspan=4,sticky='w',pady=(0,8))
        ttk.Label(self.tab_setup,text='每個平台：按「開啟設定瀏覽器」→ 在跳出的專用瀏覽器登入並切到你想每天擷取的 Insights 畫面 → 回來按「記住目前網址」。').grid(row=1,column=0,columnspan=4,sticky='w',pady=(0,12))
        r=2
        for p in PLATFORMS:
            ttk.Label(self.tab_setup,text=LABELS[p],width=12).grid(row=r,column=0,sticky='w',pady=5)
            ttk.Entry(self.tab_setup,textvariable=self.url_vars[p],width=62).grid(row=r,column=1,sticky='ew',padx=6)
            ttk.Button(self.tab_setup,text='開啟設定瀏覽器',command=lambda x=p:self.open_setup_browser(x)).grid(row=r,column=2,padx=4)
            ttk.Button(self.tab_setup,text='記住目前網址',command=lambda x=p:self.remember_url(x)).grid(row=r,column=3,padx=4)
            r+=1
        self.tab_setup.columnconfigure(1,weight=1)
        ttk.Separator(self.tab_setup).grid(row=r,column=0,columnspan=4,sticky='ew',pady=14); r+=1
        ttk.Label(self.tab_setup,text='B. GitHub Dashboard 同步（選用）',font=('Microsoft JhengHei UI',13,'bold')).grid(row=r,column=0,columnspan=4,sticky='w'); r+=1
        ttk.Label(self.tab_setup,text='建議先用 GitHub Desktop 把網站 Repository Clone 到這台電腦，再選那個資料夾。').grid(row=r,column=0,columnspan=4,sticky='w',pady=(2,8)); r+=1
        ttk.Label(self.tab_setup,text='本機 Repository').grid(row=r,column=0,sticky='w')
        ttk.Entry(self.tab_setup,textvariable=self.repo_var).grid(row=r,column=1,columnspan=2,sticky='ew',padx=6)
        ttk.Button(self.tab_setup,text='選擇資料夾',command=self.pick_repo).grid(row=r,column=3); r+=1
        ttk.Checkbutton(self.tab_setup,text='每日擷取成功後自動 commit / push 到 GitHub',variable=self.git_var).grid(row=r,column=1,columnspan=3,sticky='w',pady=6); r+=1
        ttk.Label(self.tab_setup,text='本單位私訊名稱').grid(row=r,column=0,sticky='w')
        ttk.Entry(self.tab_setup,textvariable=self.own_names_var).grid(row=r,column=1,columnspan=3,sticky='ew',padx=6)
        ttk.Label(self.tab_setup,text='用逗號分隔，例如：高雄市政府運動發展局, 官方IG帳號名稱；用來排除自己回覆。',foreground='#666').grid(row=r+1,column=1,columnspan=3,sticky='w',padx=6); r+=2
        ttk.Label(self.tab_setup,text='每日執行時間').grid(row=r,column=0,sticky='w')
        ttk.Entry(self.tab_setup,textvariable=self.time_var,width=12).grid(row=r,column=1,sticky='w',padx=6)
        ttk.Button(self.tab_setup,text='儲存設定',command=self.save_settings).grid(row=r,column=2,padx=4)
        ttk.Button(self.tab_setup,text='安裝每日排程',command=self.install_schedule).grid(row=r,column=3,padx=4); r+=1
        ttk.Button(self.tab_setup,text='移除每日排程',command=self.remove_schedule).grid(row=r,column=3,pady=4)

    def _build_import(self):
        ttk.Label(self.tab_import,text='Meta 每月官方匯出檔 → 自動整理',font=('Microsoft JhengHei UI',13,'bold')).pack(anchor='w')
        ttk.Label(self.tab_import,text='FB／IG／Threads 的 CSV、XLSX 可以直接匯入；欄位名稱不同時會用常見中英文欄位自動比對。').pack(anchor='w',pady=(2,10))
        f=ttk.LabelFrame(self.tab_import,text='內容成效（貼文／Reels／限動／Threads）',padding=12); f.pack(fill='x',pady=6)
        self.content_pf=tk.StringVar(value='auto')
        ttk.Label(f,text='平台').pack(side='left'); ttk.Combobox(f,textvariable=self.content_pf,values=['auto','facebook','instagram','threads'],state='readonly',width=12).pack(side='left',padx=6)
        ttk.Button(f,text='選擇 CSV / XLSX 並匯入',command=self.import_content).pack(side='left',padx=6)
        ttk.Label(f,text='系統會依活動名稱／關鍵字自動掛活動；低信心項目留給網站人工確認。').pack(side='left',padx=10)
        m=ttk.LabelFrame(self.tab_import,text='私訊／後台詢問（本機匿名分析）',padding=12); m.pack(fill='x',pady=12)
        self.msg_pf=tk.StringVar(value='auto')
        ttk.Label(m,text='平台').pack(side='left'); ttk.Combobox(m,textvariable=self.msg_pf,values=['auto','facebook','instagram','threads'],state='readonly',width=12).pack(side='left',padx=6)
        ttk.Button(m,text='選擇官方 ZIP / JSON / 資料夾',command=self.import_messages).pack(side='left',padx=6)
        ttk.Label(m,text='原文只存於此電腦；GitHub 僅保存「活動×問題類型×件數」。').pack(side='left',padx=10)
        info=ttk.LabelFrame(self.tab_import,text='私訊本機校正（不會上傳原文）',padding=12); info.pack(fill='both',expand=True,pady=8)
        head=ttk.Frame(info); head.pack(fill='x')
        ttk.Button(head,text='載入最近私訊分析',command=self.load_private_review).pack(side='left')
        ttk.Label(head,text='選一筆後可修正活動、問題分類或排除；按「儲存校正」才會重建匿名統計。').pack(side='left',padx=10)
        cols=('date','platform','activity','topic','text')
        self.private_tree=ttk.Treeview(info,columns=cols,show='headings',height=8)
        for c,t,w in [('date','日期',90),('platform','平台',80),('activity','活動',150),('topic','問題分類',120),('text','詢問內容（僅本機）',390)]:
            self.private_tree.heading(c,text=t); self.private_tree.column(c,width=w,anchor='w')
        self.private_tree.pack(fill='both',expand=True,pady=8); self.private_tree.bind('<<TreeviewSelect>>',self.on_private_select)
        edit=ttk.Frame(info); edit.pack(fill='x')
        self.private_activity=tk.StringVar(value=''); self.private_topic=tk.StringVar(value='other'); self.private_include=tk.BooleanVar(value=True)
        ttk.Label(edit,text='活動').pack(side='left'); self.private_activity_cb=ttk.Combobox(edit,textvariable=self.private_activity,state='readonly',width=28); self.private_activity_cb.pack(side='left',padx=5)
        ttk.Label(edit,text='分類').pack(side='left',padx=(10,0)); self.private_topic_cb=ttk.Combobox(edit,textvariable=self.private_topic,state='readonly',width=18); self.private_topic_cb['values']=[k for k in TOPICS]; self.private_topic_cb.pack(side='left',padx=5)
        ttk.Checkbutton(edit,text='納入統計',variable=self.private_include).pack(side='left',padx=10)
        ttk.Button(edit,text='套用到選取資料',command=self.apply_private_edit).pack(side='left',padx=5)
        ttk.Button(edit,text='儲存校正並更新匿名統計',command=self.save_private_review).pack(side='right')
        ttk.Label(info,text='原始私訊與姓名只留在本機 LocalAppData/SocialImpactCollector/private；GitHub 只收到匿名件數。',foreground='#666').pack(anchor='w',pady=(4,0))

    def _build_status(self):
        top=ttk.Frame(self.tab_status); top.pack(fill='x')
        ttk.Button(top,text='▶ 立即擷取三平台',command=self.collect_now).pack(side='left',padx=(0,6))
        ttk.Button(top,text='以可見瀏覽器測試',command=lambda:self.collect_now(headed=True)).pack(side='left',padx=6)
        ttk.Button(top,text='立即同步 GitHub',command=self.git_now).pack(side='left',padx=6)
        ttk.Button(top,text='開啟本機資料資料夾',command=self.open_data_dir).pack(side='left',padx=6)
        self.log=tk.Text(self.tab_status,height=28,wrap='word',font=('Consolas',10)); self.log.pack(fill='both',expand=True,pady=12)
        self.log.insert('end','每日自動蒐集只會讀取你已登入且有權限看到的 Insights 畫面。\n建議第一次用「以可見瀏覽器測試」確認三平台都能正常顯示。\n')

    def save_settings(self):
        for p in PLATFORMS: self.cfg['platforms'][p]['insights_url']=self.url_vars[p].get().strip()
        self.cfg['dashboard_repo_path']=self.repo_var.get().strip(); self.cfg['daily_time']=self.time_var.get().strip(); self.cfg['auto_git_sync']=bool(self.git_var.get())
        self.cfg['own_sender_names']=[x.strip() for x in self.own_names_var.get().replace('，',',').split(',') if x.strip()]
        save_config(self.cfg); self.status_var.set(f'設定已儲存：{config_path()}')

    def open_setup_browser(self,p):
        self.save_settings()
        cli=Path(__file__).resolve().parent/'collector_cli.py'
        py=sys.executable
        try:
            flags=0
            if os.name=='nt': flags=getattr(subprocess,'CREATE_NEW_CONSOLE',0)
            subprocess.Popen([py,str(cli),'--setup-browser',p],cwd=str(Path(__file__).resolve().parent),creationflags=flags)
            self.status_var.set(f'{LABELS[p]} 設定瀏覽器已開啟；登入並切到 Insights 後按「記住目前網址」。')
        except Exception as e: messagebox.showerror('無法開啟',str(e))

    def remember_url(self,p):
        u=current_setup_url(p)
        if not u:
            messagebox.showwarning('尚未取得網址','請先按「開啟設定瀏覽器」，在瀏覽器內切到目標 Insights 畫面。')
            return
        self.url_vars[p].set(u); self.save_settings(); self.status_var.set(f'已記住 {LABELS[p]}：{u[:100]}')

    def pick_repo(self):
        d=filedialog.askdirectory(title='選擇 GitHub Desktop Clone 下來的網站 Repository 資料夾')
        if d: self.repo_var.set(d)

    def install_schedule(self):
        self.save_settings(); r=install_task(self.time_var.get().strip()); (messagebox.showinfo if r['ok'] else messagebox.showerror)('每日排程',r['message']); self.status_var.set(r['message'])

    def remove_schedule(self):
        r=remove_task(); (messagebox.showinfo if r['ok'] else messagebox.showerror)('每日排程',r['message']); self.status_var.set(r['message'])

    def _run_bg(self,fn,label):
        self.status_var.set(label+'…')
        def work():
            try: result=fn(); self.after(0,lambda:self.show_result(label,result))
            except Exception as e: self.after(0,lambda:messagebox.showerror(label,str(e)))
        threading.Thread(target=work,daemon=True).start()

    def show_result(self,label,result):
        txt=json.dumps(result,ensure_ascii=False,indent=2)
        self.log.insert('end',f'\n[{label}]\n{txt}\n'); self.log.see('end'); self.status_var.set(label+'完成')
        if label == '私訊匿名分析':
            self.load_private_review(result.get('private_detail'))

    def collect_now(self,headed=False):
        self.save_settings(); self._run_bg(lambda:collect_all(headed=headed), '三平台擷取')

    def git_now(self):
        self.save_settings(); self._run_bg(lambda:git_sync(), 'GitHub 同步')

    def import_content(self):
        f=filedialog.askopenfilename(title='選擇 Meta 內容成效檔',filetypes=[('資料檔','*.csv *.xlsx *.xlsm'),('CSV','*.csv'),('Excel','*.xlsx *.xlsm'),('所有檔案','*.*')])
        if f: self._run_bg(lambda:import_content_file(f,self.content_pf.get()), '內容資料匯入')

    def import_messages(self):
        f=filedialog.askopenfilename(title='選擇 Meta 私訊 ZIP / JSON',filetypes=[('Meta 匯出','*.zip *.json'),('ZIP','*.zip'),('JSON','*.json'),('所有檔案','*.*')])
        if not f:
            d=filedialog.askdirectory(title='或選擇已解壓縮的 Meta 資料夾')
            f=d
        if f: self._run_bg(lambda:import_private_messages(f,self.msg_pf.get()), '私訊匿名分析')

    def load_private_review(self, path=None):
        self.private_path, self.private_rows = load_private_rows(path)
        for i in self.private_tree.get_children(): self.private_tree.delete(i)
        acts = activity_catalog(self.cfg)
        amap = {a.get('id',''): a.get('name','') for a in acts}
        self.private_activity_map={'未歸類':''}; self.private_activity_map.update({a.get('name',''):a.get('id','') for a in acts})
        self.private_activity_cb['values'] = list(self.private_activity_map.keys())
        for idx,r in enumerate(self.private_rows):
            topic_label = TOPICS.get(r.get('topic','other'), (r.get('topic','other'),[]))[0]
            text = str(r.get('text','')).replace('\n',' ')[:90]
            prefix = '' if r.get('included',True) else '〔排除〕 '
            self.private_tree.insert('', 'end', iid=str(idx), values=(r.get('date',''),r.get('platform',''),amap.get(r.get('activity_id',''),'未歸類'),topic_label,prefix+text))
        self.status_var.set(f'已載入 {len(self.private_rows)} 筆本機私訊明細' if self.private_rows else '尚無私訊本機分析資料')

    def on_private_select(self, _event=None):
        sel=self.private_tree.selection()
        if not sel: return
        r=self.private_rows[int(sel[0])]
        acts={a.get('id',''):a.get('name','') for a in activity_catalog(self.cfg)}
        topic_label=TOPICS.get(r.get('topic','other'),('其他',[]))[0]
        self.private_activity.set(acts.get(r.get('activity_id',''),'未歸類')); self.private_topic.set(topic_label); self.private_include.set(r.get('included',True))

    def apply_private_edit(self):
        sel=self.private_tree.selection()
        if not sel: return
        idx=int(sel[0]); r=self.private_rows[idx]
        r['activity_id']=self.private_activity_map.get(self.private_activity.get(),''); r['topic']=self.private_topic_map.get(self.private_topic.get(),'other'); r['included']=bool(self.private_include.get()); r['confidence']='manual'
        acts={a.get('id',''):a.get('name','') for a in activity_catalog(self.cfg)}
        topic_label=TOPICS.get(r['topic'],(r['topic'],[]))[0]
        prefix='' if r['included'] else '〔排除〕 '
        self.private_tree.item(sel[0],values=(r.get('date',''),r.get('platform',''),acts.get(r.get('activity_id',''),'未歸類'),topic_label,prefix+str(r.get('text','')).replace('\n',' ')[:90]))
        self.status_var.set('已套用到本機明細；記得按「儲存校正並更新匿名統計」')

    def save_private_review(self):
        if not self.private_path:
            messagebox.showwarning('沒有資料','請先匯入或載入私訊分析資料'); return
        r=save_private_rows(self.private_rows,self.private_path)
        (messagebox.showinfo if r.get('ok') else messagebox.showerror)('私訊校正',r.get('message',''))
        self.status_var.set(r.get('message',''))

    def open_data_dir(self):
        p=app_data_dir()
        if os.name=='nt': os.startfile(str(p))
        elif sys.platform=='darwin': subprocess.Popen(['open',str(p)])
        else: subprocess.Popen(['xdg-open',str(p)])

    def on_close(self):
        self.save_settings(); self.destroy()

if __name__=='__main__': App().mainloop()
