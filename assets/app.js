const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

const PLATFORM = {
  facebook: {label:'Facebook', color:'#1877f2'},
  instagram: {label:'Instagram', color:'#c13584'},
  threads: {label:'Threads', color:'#242424'}
};

const state = {
  data:null,
  platforms:new Set(['facebook','instagram','threads']),
  start:null,end:null,compare:true,
  charts:{},
  view:'overview'
};

const fmt = new Intl.NumberFormat('zh-TW');
const fmtCompact = new Intl.NumberFormat('zh-TW',{notation:'compact',maximumFractionDigits:1});
const fmtPct = (n) => `${(Number(n)||0).toFixed(2)}%`;
const n = (v) => Number.isFinite(Number(v)) ? Number(v) : 0;
const dateOnly = (v) => String(v||'').slice(0,10);
const toDate = (v) => new Date(`${dateOnly(v)}T00:00:00`);
const dateAdd = (d, days) => { const x=new Date(d); x.setDate(x.getDate()+days); return x; };
const isoDate = (d) => d.toISOString().slice(0,10);
const esc = (s='') => String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const platformLabel = (p) => PLATFORM[p]?.label || p;
const colorFor = (p) => PLATFORM[p]?.color || '#6f7d92';
const compact = (v) => fmtCompact.format(Math.round(n(v)));

function showToast(text){
  const el=$('#toast'); el.textContent=text; el.classList.add('show');
  clearTimeout(showToast.t); showToast.t=setTimeout(()=>el.classList.remove('show'),1800);
}

function postInteractions(p){
  if (p.interactions != null) return n(p.interactions);
  return ['likes','comments','replies','shares','saves','reposts','quotes','clicks'].reduce((s,k)=>s+n(p[k]),0);
}
function rowInteractions(r){
  if (r.interactions != null) return n(r.interactions);
  return ['likes','comments','replies','shares','saves','reposts','quotes','clicks'].reduce((s,k)=>s+n(r[k]),0);
}
function postEngagement(p){
  const base=n(p.views)||n(p.reach); return base ? postInteractions(p)/base*100 : 0;
}
function rowNet(r){ return n(r.follows)-n(r.unfollows); }

function filteredDaily(start=state.start,end=state.end){
  return state.data.daily.filter(r => state.platforms.has(r.platform) && r.date>=start && r.date<=end);
}
function filteredPosts(start=state.start,end=state.end){
  return state.data.posts.filter(p => state.platforms.has(p.platform) && dateOnly(p.timestamp)>=start && dateOnly(p.timestamp)<=end);
}
function metricsFor(start=state.start,end=state.end){
  const rows=filteredDaily(start,end), posts=filteredPosts(start,end);
  const views=rows.reduce((s,r)=>s+n(r.views),0);
  const reachRows=rows.filter(r=>r.reach!=null);
  const reach=reachRows.length?reachRows.reduce((s,r)=>s+n(r.reach),0):null;
  const interactions=rows.reduce((s,r)=>s+rowInteractions(r),0);
  const profileViews=rows.reduce((s,r)=>s+n(r.profile_views),0);
  const netFollowers=followerGrowth(rows);
  return {views,reach,interactions,profileViews,netFollowers,posts:posts.length,engagement:views?interactions/views*100:0};
}
function followerGrowth(rows){
  const groups=groupBy(rows,r=>r.account_key);
  let total=0;
  for(const list of Object.values(groups)){
    const sorted=[...list].sort((a,b)=>a.date.localeCompare(b.date));
    const withFollowers=sorted.filter(r=>r.followers!=null);
    if(withFollowers.length>=2) total += n(withFollowers.at(-1).followers)-n(withFollowers[0].followers);
    else total += sorted.reduce((s,r)=>s+rowNet(r),0);
  }
  return total;
}
function groupBy(arr, fn){ return arr.reduce((o,x)=>{const k=fn(x);(o[k]??=[]).push(x);return o;},{}); }

function previousRange(){
  const s=toDate(state.start), e=toDate(state.end);
  const days=Math.round((e-s)/86400000)+1;
  const pe=dateAdd(s,-1), ps=dateAdd(pe,-days+1);
  return {start:isoDate(ps), end:isoDate(pe)};
}
function deltaInfo(current, previous, invert=false){
  if(!state.compare || previous==null) return {text:'—',cls:'flat'};
  if(previous===0) return current===0?{text:'0%',cls:'flat'}:{text:'新增',cls:'up'};
  const d=(current-previous)/Math.abs(previous)*100;
  const good=invert?d<0:d>0;
  return {text:`${d>0?'+':''}${d.toFixed(1)}%`,cls:Math.abs(d)<.05?'flat':good?'up':'down'};
}

function initFilters(){
  const dates=state.data.daily.map(r=>r.date).filter(Boolean).sort();
  const maxDate=dates.at(-1) || dateOnly(new Date().toISOString());
  const yr=maxDate.slice(0,4);
  state.start=`${yr}-01-01`; state.end=maxDate;
  $('#startDate').value=state.start; $('#endDate').value=state.end;

  const available=[...new Set(state.data.accounts.map(a=>a.platform))];
  state.platforms=new Set(available);
  $('#platformFilters').innerHTML=available.map(p=>`<button class="platform-chip active" data-platform="${p}">${platformLabel(p)}</button>`).join('');
}

function bindEvents(){
  $$('.nav-item').forEach(b=>b.addEventListener('click',()=>switchView(b.dataset.view)));
  $('#menuBtn').addEventListener('click',()=>$('#sidebar').classList.toggle('open'));
  $('#rangePresets').addEventListener('click',(e)=>{
    const b=e.target.closest('button'); if(!b)return;
    $$('#rangePresets button').forEach(x=>x.classList.toggle('active',x===b));
    setPreset(b.dataset.range);
  });
  $('#startDate').addEventListener('change',customRange);
  $('#endDate').addEventListener('change',customRange);
  $('#platformFilters').addEventListener('click',(e)=>{
    const b=e.target.closest('button');if(!b)return; const p=b.dataset.platform;
    if(state.platforms.has(p) && state.platforms.size>1){state.platforms.delete(p);b.classList.remove('active');}
    else if(!state.platforms.has(p)){state.platforms.add(p);b.classList.add('active');}
    renderAll();
  });
  $('#compareToggle').addEventListener('change',e=>{state.compare=e.target.checked;renderAll();});
  $('#overviewTrendMetric').addEventListener('change',renderOverviewCharts);
  $('#contentMetric').addEventListener('change',renderContentTypeChart);
  $('#topPostMetric').addEventListener('change',renderTopPosts);
  $('#topPostLimit').addEventListener('change',renderTopPosts);
  $('#printBtn').addEventListener('click',()=>window.print());
  $('#copySummaryBtn').addEventListener('click',copySummary);
  $('#exportCsvBtn').addEventListener('click',exportSummaryCsv);
  $('#downloadJsonBtn').addEventListener('click',downloadJson);
}
function switchView(view){
  state.view=view;
  $$('.nav-item').forEach(x=>x.classList.toggle('active',x.dataset.view===view));
  $$('.view').forEach(x=>x.classList.toggle('active',x.id===`view-${view}`));
  const names={overview:'社群效益總覽',trend:'社群趨勢分析',content:'內容效益分析',report:'經費成果報告',data:'資料狀態'};
  $('#pageTitle').textContent=names[view]||names.overview;
  $('#sidebar').classList.remove('open');
  setTimeout(()=>Object.values(state.charts).forEach(c=>c?.resize()),50);
}
function setPreset(range){
  const max=toDate([...state.data.daily.map(r=>r.date)].sort().at(-1));
  let start;
  if(range==='30') start=dateAdd(max,-29);
  else if(range==='90') start=dateAdd(max,-89);
  else if(range==='year') start=new Date(max.getFullYear(),0,1);
  else start=new Date(max.getFullYear(),0,1);
  state.start=isoDate(start);state.end=isoDate(max);
  $('#startDate').value=state.start;$('#endDate').value=state.end;renderAll();
}
function customRange(){
  const s=$('#startDate').value,e=$('#endDate').value;if(!s||!e||s>e)return;
  state.start=s;state.end=e;$$('#rangePresets button').forEach(x=>x.classList.remove('active'));renderAll();
}

function renderAll(){
  renderMetricCards();renderOverviewCharts();renderInsights();renderMonthlyTable();
  renderTrend();renderContent();renderReport();renderDataStatus();
}

function renderMetricCards(){
  const cur=metricsFor(); const pr=previousRange(); const prev=state.compare?metricsFor(pr.start,pr.end):null;
  const cards=[
    ['觀看／曝光',cur.views,prev?.views,'跨平台量體','views'],
    ['互動總數',cur.interactions,prev?.interactions,'按平台可取得互動加總','interactions'],
    ['平均互動率',cur.engagement,prev?.engagement,'互動 ÷ 觀看','pct'],
    ['淨追蹤成長',cur.netFollowers,prev?.netFollowers,'期間追蹤者增加量','followers'],
    ['內容產出',cur.posts,prev?.posts,'FB＋IG＋Threads 貼文','posts']
  ];
  $('#metricCards').innerHTML=cards.map(([label,val,pv,foot,type])=>{
    const d=deltaInfo(val,pv); const display=type==='pct'?fmtPct(val):fmt.format(Math.round(val));
    return `<article class="metric-card"><div class="metric-label"><span>${label}</span><span class="delta ${d.cls}">${d.text}</span></div><div class="metric-value">${display}</div><div class="metric-foot"><span>${foot}</span><span>${state.compare?'較前期':''}</span></div></article>`;
  }).join('');
}

function aggregateSeries(metric){
  const rows=filteredDaily();
  const span=Math.round((toDate(state.end)-toDate(state.start))/86400000)+1;
  const bucket=span>180?7:span>90?3:1;
  const groups={};
  for(const r of rows){
    const dayIndex=Math.floor((toDate(r.date)-toDate(state.start))/86400000);
    const bucketStart=isoDate(dateAdd(toDate(state.start),Math.floor(dayIndex/bucket)*bucket));
    const key=`${bucketStart}|${r.platform}`;
    if(!groups[key]) groups[key]={date:bucketStart,platform:r.platform,value:0};
    const value=metric==='netFollowers'?rowNet(r):metric==='interactions'?rowInteractions(r):n(r[metric]);
    groups[key].value+=value;
  }
  const dates=[...new Set(Object.values(groups).map(x=>x.date))].sort();
  return {dates,datasets:[...state.platforms].map(p=>({label:platformLabel(p),platform:p,data:dates.map(d=>groups[`${d}|${p}`]?.value||0)}))};
}
function chart(id,type,config){
  if(state.charts[id]) state.charts[id].destroy();
  const ctx=document.getElementById(id); if(!ctx || typeof Chart==='undefined')return;
  state.charts[id]=new Chart(ctx,{type,data:config.data,options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,usePointStyle:true,font:{size:10}}},tooltip:{callbacks:config.tooltipCallbacks||{}}},scales:config.scales||{},...config.options}});
}
function lineChart(id,metric){
  const s=aggregateSeries(metric);
  chart(id,'line',{data:{labels:s.dates,datasets:s.datasets.map(ds=>({label:ds.label,data:ds.data,borderColor:colorFor(ds.platform),backgroundColor:colorFor(ds.platform),borderWidth:2,pointRadius:0,tension:.25}))},
    scales:{x:{grid:{display:false},ticks:{maxTicksLimit:8,font:{size:9}}},y:{beginAtZero:true,grid:{color:'#edf0f5'},ticks:{callback:v=>compact(v),font:{size:9}}}}});
}
function renderOverviewCharts(){
  lineChart('overviewTrendChart',$('#overviewTrendMetric').value);
  const rows=filteredDaily(); const grouped=groupBy(rows,r=>r.platform);
  const labels=[...state.platforms].map(platformLabel);
  const data=[...state.platforms].map(p=>grouped[p]?.reduce((s,r)=>s+n(r.views),0)||0);
  chart('platformChart','doughnut',{data:{labels,datasets:[{data,backgroundColor:[...state.platforms].map(colorFor),borderWidth:0}]},options:{cutout:'68%'}});
}

function renderInsights(){
  const rows=filteredDaily(),posts=filteredPosts();
  const byP=groupBy(rows,r=>r.platform);
  const perf=[...state.platforms].map(p=>({p,views:(byP[p]||[]).reduce((s,r)=>s+n(r.views),0),inter:(byP[p]||[]).reduce((s,r)=>s+rowInteractions(r),0),growth:followerGrowth(byP[p]||[])}));
  const best=perf.sort((a,b)=>b.views-a.views)[0];
  $('#bestPlatformTitle').textContent=best?platformLabel(best.p):'—';
  $('#bestPlatformText').textContent=best?`貢獻 ${compact(best.views)} 次觀看／曝光，占本期主要量體。`:'目前沒有資料';
  const top=[...posts].sort((a,b)=>postInteractions(b)-postInteractions(a))[0];
  $('#bestContentTitle').textContent=top?`${platformLabel(top.platform)}｜${compact(postInteractions(top))} 互動`:'—';
  $('#bestContentText').textContent=top?(top.text||'無貼文文字').slice(0,76):'目前沒有貼文資料';
  const grow=[...perf].sort((a,b)=>b.growth-a.growth)[0];
  $('#growthTitle').textContent=grow?`${platformLabel(grow.p)} +${fmt.format(Math.round(grow.growth))}`:'—';
  $('#growthText').textContent=grow?'本期淨追蹤成長最高的平台，可作為後續資源配置參考。':'目前沒有追蹤成長資料';
}

function monthlyData(){
  const rows=filteredDaily(), posts=filteredPosts();
  const groups=groupBy(rows,r=>r.date.slice(0,7));
  const postGroups=groupBy(posts,p=>dateOnly(p.timestamp).slice(0,7));
  return Object.keys(groups).sort().map(m=>{
    const rr=groups[m];const views=rr.reduce((s,r)=>s+n(r.views),0);const inter=rr.reduce((s,r)=>s+rowInteractions(r),0);
    return {month:m,views,interactions:inter,growth:followerGrowth(rr),posts:(postGroups[m]||[]).length,engagement:views?inter/views*100:0};
  });
}
function renderMonthlyTable(){
  const data=monthlyData();
  $('#monthlyTable').innerHTML=`<thead><tr><th>月份</th><th class="num">觀看／曝光</th><th class="num">互動</th><th class="num">互動率</th><th class="num">淨追蹤</th><th class="num">貼文數</th></tr></thead><tbody>${data.map(r=>`<tr><td><strong>${r.month}</strong></td><td class="num">${fmt.format(Math.round(r.views))}</td><td class="num">${fmt.format(Math.round(r.interactions))}</td><td class="num">${fmtPct(r.engagement)}</td><td class="num">${r.growth>=0?'+':''}${fmt.format(Math.round(r.growth))}</td><td class="num">${r.posts}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">無資料</td></tr>'}</tbody>`;
}

function renderTrend(){
  lineChart('viewsTrendChart','views');lineChart('interactionsTrendChart','interactions');lineChart('followersChart','netFollowers');
  const cur=metricsFor();const pr=previousRange();const prev=metricsFor(pr.start,pr.end);
  const items=[['觀看／曝光',cur.views,prev.views],['互動總數',cur.interactions,prev.interactions],['平均互動率',cur.engagement,prev.engagement,true],['淨追蹤成長',cur.netFollowers,prev.netFollowers],['內容產出',cur.posts,prev.posts]];
  $('#comparisonPanel').innerHTML=items.map(([label,v,p,isPct])=>{const d=deltaInfo(v,p);return `<div class="comparison-row"><div><strong>${label}</strong><span>前期 ${isPct?fmtPct(p):fmt.format(Math.round(p))}</span></div><div class="delta ${d.cls}">${d.text}</div></div>`}).join('');
}

function renderContent(){
  const posts=filteredPosts();
  const views=posts.reduce((s,p)=>s+n(p.views),0), inter=posts.reduce((s,p)=>s+postInteractions(p),0);
  const avg=posts.length?views/posts.length:0, er=views?inter/views*100:0;
  const high=posts.filter(p=>postEngagement(p)>=er*1.5).length;
  $('#contentKpis').innerHTML=[['期間貼文',posts.length],['平均單篇觀看',compact(avg)],['內容互動率',fmtPct(er)],['高效內容篇數',high]].map(([a,b])=>`<div class="mini-kpi"><span>${a}</span><strong>${b}</strong></div>`).join('');
  renderContentTypeChart();renderHeatmap();renderTopPosts();
}
function renderContentTypeChart(){
  const posts=filteredPosts();const metric=$('#contentMetric').value;const g=groupBy(posts,p=>`${platformLabel(p.platform)}｜${p.media_type||'POST'}`);
  const rows=Object.entries(g).map(([k,v])=>{
    let value=0;
    if(metric==='views')value=v.reduce((s,p)=>s+n(p.views),0)/v.length;
    else if(metric==='interactions')value=v.reduce((s,p)=>s+postInteractions(p),0)/v.length;
    else value=v.reduce((s,p)=>s+postEngagement(p),0)/v.length;
    return {k,value};
  }).sort((a,b)=>b.value-a.value).slice(0,10);
  chart('contentTypeChart','bar',{data:{labels:rows.map(x=>x.k),datasets:[{label:metric==='engagement'?'平均互動率 (%)':metric==='views'?'平均觀看':'平均互動',data:rows.map(x=>x.value),backgroundColor:'#5578df',borderRadius:6}]},scales:{x:{grid:{display:false},ticks:{font:{size:9}}},y:{beginAtZero:true,grid:{color:'#edf0f5'},ticks:{callback:v=>metric==='engagement'?`${v}%`:compact(v),font:{size:9}}}},options:{plugins:{legend:{display:false}}}});
}
function renderHeatmap(){
  const posts=filteredPosts(); const days=['一','二','三','四','五','六','日']; const ranges=['00–05','06–11','12–17','18–23'];
  const vals={};
  posts.forEach(p=>{const d=new Date(p.timestamp);let wd=d.getDay();wd=wd===0?6:wd-1;const rb=Math.floor(d.getHours()/6);const k=`${rb}-${wd}`;(vals[k]??=[]).push(postInteractions(p));});
  const avgs=Object.fromEntries(Object.entries(vals).map(([k,v])=>[k,v.reduce((a,b)=>a+b,0)/v.length]));
  const max=Math.max(1,...Object.values(avgs));
  let html='<div class="heatmap-grid"><div class="heat-cell header"></div>'+days.map(d=>`<div class="heat-cell header">週${d}</div>`).join('');
  ranges.forEach((r,ri)=>{html+=`<div class="heat-cell header">${r}</div>`;days.forEach((_,di)=>{const v=avgs[`${ri}-${di}`]||0;const level=v?Math.min(5,Math.ceil(v/max*5)):0;html+=`<div class="heat-cell ${level?`level-${level}`:''}" title="平均互動 ${Math.round(v)}">${v?compact(v):'—'}</div>`});});
  html+='</div>';$('#heatmap').innerHTML=html;
}
function renderTopPosts(){
  const metric=$('#topPostMetric').value,limit=n($('#topPostLimit').value)||10;
  const value=p=>metric==='engagement'?postEngagement(p):metric==='interactions'?postInteractions(p):n(p.views);
  const posts=[...filteredPosts()].sort((a,b)=>value(b)-value(a)).slice(0,limit);
  $('#topPostsTable').innerHTML=`<thead><tr><th>#</th><th>平台</th><th>發布日</th><th>內容</th><th>類型</th><th class="num">觀看</th><th class="num">互動</th><th class="num">互動率</th></tr></thead><tbody>${posts.map((p,i)=>`<tr><td>${i+1}</td><td><span class="platform-dot" style="background:${colorFor(p.platform)}"></span>${platformLabel(p.platform)}</td><td>${dateOnly(p.timestamp)}</td><td class="post-title">${p.permalink&&p.permalink!=='#'?`<a href="${esc(p.permalink)}" target="_blank" rel="noopener">${esc((p.text||'無文字').slice(0,95))}</a>`:esc((p.text||'無文字').slice(0,95))}</td><td>${esc(p.media_type||'—')}</td><td class="num">${fmt.format(Math.round(n(p.views)))}</td><td class="num">${fmt.format(Math.round(postInteractions(p)))}</td><td class="num">${fmtPct(postEngagement(p))}</td></tr>`).join('')||'<tr><td colspan="8" class="empty">本期間無貼文資料</td></tr>'}</tbody>`;
}

function renderReport(){
  const cur=metricsFor();const project=state.data.meta?.project||{};const goals=project.goals||{};
  const growth=cur.netFollowers, values={views:cur.views,interactions:cur.interactions,followers_growth:growth,posts:cur.posts};
  const labels={views:'年度觀看／曝光',interactions:'年度互動',followers_growth:'追蹤者淨成長',posts:'內容產出'};
  $('#goalProgress').innerHTML=Object.entries(labels).map(([k,label])=>{const goal=n(goals[k]);const val=n(values[k]);const pct=goal?val/goal*100:0;return `<div class="progress-item"><div class="progress-top"><strong>${label}</strong><span>${fmt.format(Math.round(val))} / ${goal?fmt.format(Math.round(goal)):'未設定'}</span></div><div class="progress-track"><div class="progress-fill" style="width:${Math.min(100,pct)}%"></div></div><div class="hint">${goal?`達成 ${pct.toFixed(1)}%`:'請在 config/accounts.json 設定年度目標'}</div></div>`}).join('');
  $('#reportSummary').innerHTML=buildReportSummary(cur,project);
  renderEvidenceTable();
}
function buildReportSummary(cur,project){
  const org=esc(project.organization||'本單位');const y=project.fiscal_year||state.end.slice(0,4);const pr=previousRange();const prev=metricsFor(pr.start,pr.end);const dv=deltaInfo(cur.views,prev.views),di=deltaInfo(cur.interactions,prev.interactions);
  const posts=filteredPosts();const top=[...posts].sort((a,b)=>postInteractions(b)-postInteractions(a))[0];
  return `<p><strong>${org} ${y} 年社群經營成果：</strong>於 ${state.start} 至 ${state.end} 期間，Facebook、Instagram 與 Threads 共產出 <strong>${fmt.format(cur.posts)}</strong> 則內容，累積 <strong>${fmt.format(Math.round(cur.views))}</strong> 次觀看／曝光及 <strong>${fmt.format(Math.round(cur.interactions))}</strong> 次互動，期間淨增加 <strong>${fmt.format(Math.round(cur.netFollowers))}</strong> 名追蹤者。</p>
  <p>與前一等長期間相比，觀看／曝光為 <strong class="delta ${dv.cls}">${dv.text}</strong>，互動為 <strong class="delta ${di.cls}">${di.text}</strong>；整體平均互動率約 <strong>${fmtPct(cur.engagement)}</strong>。此結果可作為社群內容持續投入、跨平台經營及後續宣傳資源配置之量化依據。</p>
  ${top?`<p>本期高互動內容以 <strong>${platformLabel(top.platform)}</strong> 貼文表現最突出，單篇累積約 <strong>${fmt.format(Math.round(postInteractions(top)))}</strong> 次互動，可作為後續主題、素材形式與發文策略優化之參考。</p>`:''}
  <p class="hint">註：跨平台指標定義不同，本摘要的「觀看／曝光」為統一量體欄位；正式對外或核銷成果文件建議同步附平台別明細。</p>`;
}
function platformMetrics(p){
  const saved=new Set(state.platforms);state.platforms=new Set([p]);const m=metricsFor();state.platforms=saved;return m;
}
function renderEvidenceTable(){
  const rows=[...state.platforms].map(p=>({p,...platformMetrics(p)}));
  const total=metricsFor();
  $('#evidenceTable').innerHTML=`<thead><tr><th>平台</th><th class="num">觀看／曝光</th><th class="num">觸及*</th><th class="num">互動</th><th class="num">互動率</th><th class="num">淨追蹤</th><th class="num">內容</th></tr></thead><tbody>${rows.map(r=>`<tr><td><strong>${platformLabel(r.p)}</strong></td><td class="num">${fmt.format(Math.round(r.views))}</td><td class="num">${r.reach==null?'—':fmt.format(Math.round(r.reach))}</td><td class="num">${fmt.format(Math.round(r.interactions))}</td><td class="num">${fmtPct(r.engagement)}</td><td class="num">${r.netFollowers>=0?'+':''}${fmt.format(Math.round(r.netFollowers))}</td><td class="num">${r.posts}</td></tr>`).join('')}<tr><td><strong>合計</strong></td><td class="num"><strong>${fmt.format(Math.round(total.views))}</strong></td><td class="num">${total.reach==null?'—':fmt.format(Math.round(total.reach))}</td><td class="num"><strong>${fmt.format(Math.round(total.interactions))}</strong></td><td class="num"><strong>${fmtPct(total.engagement)}</strong></td><td class="num"><strong>${total.netFollowers>=0?'+':''}${fmt.format(Math.round(total.netFollowers))}</strong></td><td class="num"><strong>${total.posts}</strong></td></tr></tbody>`;
}

function renderDataStatus(){
  $('#accountStatus').innerHTML=state.data.accounts.map(a=>`<article class="account-card"><div class="account-head"><div class="platform-icon ${a.platform}">${a.platform==='facebook'?'f':a.platform==='instagram'?'IG':'@'}</div><div><h3>${esc(a.label||a.name||a.key)}</h3><div class="username">${a.username?'@'+esc(a.username):esc(a.id||'')}</div></div></div><div class="account-stat"><span>目前追蹤者</span><strong>${fmt.format(Math.round(n(a.followers)))}</strong></div><div class="account-stat"><span>資料狀態</span><span class="${a.status==='demo'?'status-demo':'status-ok'}">${a.status==='demo'?'示範資料':'已連線'}</span></div></article>`).join('');
  const logs=[...(state.data.collection_log||[])].reverse();
  $('#collectionLogTable').innerHTML=`<thead><tr><th>時間</th><th class="num">帳號</th><th class="num">日資料</th><th class="num">貼文</th><th class="num">警告</th></tr></thead><tbody>${logs.map(l=>`<tr><td>${esc(String(l.time||'').replace('T',' ').slice(0,19))}</td><td class="num">${n(l.accounts_ok)}</td><td class="num">${n(l.daily_rows)}</td><td class="num">${n(l.posts)}</td><td class="num">${n(l.warnings)}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">尚無紀錄</td></tr>'}</tbody>`;
  const warnings=state.data.warnings||[];$('#warningCount').textContent=`${warnings.length} 筆`;
  $('#warningsList').innerHTML=warnings.length?warnings.slice().reverse().map(w=>`<div class="warning-item"><strong>${esc(w.account_key||'system')}｜${esc(w.purpose||'warning')}</strong><div>${esc(w.message||'')}</div><div class="hint">${esc(w.time||'')}</div></div>`).join(''):'<div class="empty">目前沒有 API 警告。</div>';
}

function copySummary(){
  const text=$('#reportSummary').innerText;navigator.clipboard?.writeText(text).then(()=>showToast('成果摘要已複製')).catch(()=>showToast('請手動複製成果摘要'));
}
function downloadBlob(name,text,type){const blob=new Blob([text],{type});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),500);}
function csvCell(v){const s=String(v??'');return /[",\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;}
function exportSummaryCsv(){
  const rows=[['期間','平台','觀看/曝光','觸及','互動','互動率(%)','淨追蹤','內容數']];
  [...state.platforms].forEach(p=>{const m=platformMetrics(p);rows.push([`${state.start}~${state.end}`,platformLabel(p),Math.round(m.views),m.reach==null?'':Math.round(m.reach),Math.round(m.interactions),m.engagement.toFixed(2),Math.round(m.netFollowers),m.posts]);});
  const csv='\ufeff'+rows.map(r=>r.map(csvCell).join(',')).join('\n');downloadBlob(`social-impact-${state.start}-${state.end}.csv`,csv,'text/csv;charset=utf-8');showToast('CSV 已匯出');
}
function downloadJson(){downloadBlob(`social-impact-full-${state.end}.json`,JSON.stringify(state.data,null,2),'application/json');showToast('完整 JSON 已下載');}

async function init(){
  try{
    const res=await fetch(`data/analytics.json?v=${Date.now()}`);if(!res.ok)throw new Error(`HTTP ${res.status}`);
    state.data=await res.json();
    state.data.daily=state.data.daily||[];state.data.posts=state.data.posts||[];state.data.accounts=state.data.accounts||[];
    const project=state.data.meta?.project||{};
    $('#brandTitle').textContent=project.title||'社群效益戰情室';$('#brandOrg').textContent=project.organization||'Social Impact Dashboard';
    $('#dataStamp').textContent=`資料更新：${String(state.data.meta?.generated_at||'未知').replace('T',' ').replace('Z',' UTC').slice(0,25)}`;
    const demo=state.data.meta?.source==='demo';$('#sourceBadge').textContent=demo?'目前使用示範資料':'Meta API 自動更新';$('#sourceBadge').classList.toggle('demo',demo);
    initFilters();bindEvents();$('#loadingState').classList.add('hidden');$('#dashboard').classList.remove('hidden');renderAll();
  }catch(err){
    $('#loadingState').classList.add('hidden');$('#errorState').classList.remove('hidden');$('#errorState').innerHTML=`<strong>資料載入失敗</strong><br>${esc(err.message)}<br><small>若直接雙擊 index.html，瀏覽器可能阻擋 JSON。請用 GitHub Pages 或本機 HTTP server 開啟。</small>`;
  }
}

document.addEventListener('DOMContentLoaded',init);

window.addEventListener('chartjs-ready',()=>{ if(state.data) renderAll(); });
