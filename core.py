import re, json, sqlite3, csv
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, parse_qsl, urlencode, urlunsplit
from pathlib import Path

BASE='https://www.thebluebook.com'
class Node:
 def __init__(self,tag='',attrs=()): self.tag=tag; self.a=dict(attrs); self.children=[]; self.parts=[]
 def text(self): return ' '.join(' '.join(self.parts).split())
 def find(self,p):
  out=[]
  for c in self.children:
   if p(c): out.append(c)
   out.extend(c.find(p))
  return out
class Tree(HTMLParser):
 def __init__(self,s):
  super().__init__(convert_charrefs=True); self.root=Node(); self.stack=[self.root]; self.feed(s)
 def handle_starttag(self,t,a):
  n=Node(t,a); self.stack[-1].children.append(n)
  if t not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']: self.stack.append(n)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t: del self.stack[i:]; break
 def handle_data(self,d):
  if self.stack[-1].tag in ['script','style']: return
  for n in self.stack: n.parts.append(d)
def canonical(u):
 p=urlsplit(urljoin(BASE,u)); host=(p.hostname or '').lower()
 if host not in ['www.thebluebook.com','thebluebook.com']: return ''
 if p.scheme not in ['http','https']: return ''
 return urlunsplit(('https','www.thebluebook.com',p.path,urlencode(sorted(parse_qsl(p.query))),''))
def first(n,p):
 a=n.find(p); return a[0] if a else None
def phone_values(raw):
 vals=[]
 for m in re.finditer(r'(?<!\d)(?:\+?1[ .-]?)?\(?([2-9]\d{2})\)?[ .-]?([2-9]\d{2})[ .-]?(\d{4})(?!\d)(?:\s*(?:ext\.?|x|extension)\s*(\d+))?',str(raw),re.I):
  d=''.join(m.group(i) for i in [1,2,3])
  if d=='8887201710':continue
  if m.group(4): d+=' ext '+m.group(4)
  if d not in vals:vals.append(d)
 return vals
def phones(n):
 vals=[]
 def add(raw):
  for v in phone_values(raw):
   if v not in vals:vals.append(v)
 for c in n.find(lambda x:'telephone' in x.a.get('itemprop','').split() or x.a.get('href','').lower().startswith('tel:')):
  if 'fax' in (c.a.get('itemprop','')+' '+c.a.get('class','')+' '+c.a.get('aria-label','')).lower():continue
  add(c.a.get('href','')[4:] if c.a.get('href','').lower().startswith('tel:') else c.a.get('content') or c.text())
 # Visible, explicitly labelled phone blocks; never scan an entire page for digit strings.
 for c in n.find(lambda x:x.tag in ['span','div','p','li','td','dd']):
  txt=c.text(); marker=c.a.get('class','')+' '+c.a.get('id','')
  if len(txt)>220 or 'fax' in marker.lower():continue
  labelled=re.search(r'\b(?:phone|telephone|mobile|cell|office|toll.free)\s*[:.]?\s*((?:\+?1[ .-]?)?\(?[2-9]\d{2}\)?[ .-]?[2-9]\d{2}[ .-]?\d{4}(?:\s*(?:ext\.?|x)\s*\d+)?)',txt,re.I)
  if labelled:add(labelled.group(1))
  elif re.search(r'(?:^|[-_ ])(?:phone|telephone)(?:$|[-_ ])',marker,re.I) and 'fax' not in txt.lower():add(txt)
 return '; '.join(vals)
def profile_data(content,row):
 root=Tree(content).root
 def norm(v):return re.sub(r'[^a-z0-9]','',v.lower())
 expected=norm(row['company']); businesses=root.find(lambda n:n.a.get('itemtype','').rsplit('/',1)[-1] in ['LocalBusiness','Organization','GeneralContractor','HomeAndConstructionBusiness'])
 scopes=[]
 for b in businesses:
  name=first(b,lambda n:'name' in n.a.get('itemprop','').split())
  if name and norm(name.a.get('content') or name.text())==expected:scopes.append(b)
 if not scopes:
  scopes=root.find(lambda n:n.tag=='main' or n.a.get('role')=='main')
 if not scopes:
  # Remove site navigation, advertisements and footer before conservative parsing.
  def clean(n):
   n.children=[c for c in n.children if c.tag not in ['header','footer','nav','aside'] and not re.search(r'(^|[-_ ])(sponsor|advertisement|related)([-_ ]|$)',c.a.get('class',''),re.I)]
   for c in n.children:clean(c)
  clean(root);scopes=[root]
 found=[]
 for scope in scopes:
  for v in phones(scope).split('; '):
   if v and v not in found:found.append(v)
  address=first(scope,lambda n:n.a.get('itemprop')=='address')
  if address:row['address']=address.text()
  for person in scope.find(lambda n:n.a.get('itemtype','').endswith('/Person')):
   name=first(person,lambda n:n.a.get('itemprop')=='name');title=first(person,lambda n:n.a.get('itemprop')=='jobTitle')
   if name:row['contact_name']=name.text();row['contact_title']=title.text() if title else '';break
 # JSON-LD is accepted only for a business whose name matches this company's listing.
 for raw in re.findall(r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>',content,re.S|re.I):
  try:data=json.loads(raw)
  except (ValueError,TypeError):continue
  def walk(v):
   if isinstance(v,dict):
    if norm(str(v.get('name','')))==expected:
     for number in phone_values(v.get('telephone','')):
      if number not in found:found.append(number)
    for child in v.values():walk(child)
   elif isinstance(v,list):
    for child in v:walk(child)
  walk(data)
 if found:row['phone']='; '.join(dict.fromkeys([v for v in row.get('phone','').split('; ') if v]+found))
 row['status']='Phone found' if row.get('phone') else 'No public phone detected; eligible for manual retry'
 return row
def parse(s,url,category=''):
 root=Tree(s).root; cards=root.find(lambda n:'single_result_wrapper' in n.a.get('class','').split()); rows=[]
 for c in cards:
  name=first(c,lambda n:n.a.get('itemprop')=='name')
  profile=canonical(c.a.get('data-proview-url',''))
  if name and profile:
   rows.append(dict(company=name.text(),phone=phones(c),contact_name='',contact_title='',address='',category=category,profile_url=profile,source_url=url,status='Listing captured; profile pending'))
 pages=[]
 for a in root.find(lambda n:n.tag in ['a','link']):
  href=a.a.get('href',''); u=canonical(href)
  if u and urlsplit(u).path=='/search.html' and 'page' in dict(parse_qsl(urlsplit(u).query)):
   # Never follow unrelated searches.
   orig=dict(parse_qsl(urlsplit(url).query)); q=dict(parse_qsl(urlsplit(u).query))
   if all(q.get(k)==v for k,v in orig.items() if k!='page'): pages.append(u)
 pages_by_number={}
 for u in pages: pages_by_number[dict(parse_qsl(urlsplit(u).query)).get('page')]=u
 return rows,list(pages_by_number.values()),root
def search_start(u):
 u=canonical(u)
 if not u or urlsplit(u).path!='/search.html':raise ValueError('Enter a Blue Book search results URL.')
 p=urlsplit(u);q=dict(parse_qsl(p.query));q.pop('page',None)
 return urlunsplit((p.scheme,p.netloc,p.path,urlencode(sorted(q.items())),''))
class Store:
 def __init__(self,path):
  self.db=sqlite3.connect(path); self.db.execute('CREATE TABLE IF NOT EXISTS jobs(url TEXT PRIMARY KEY,kind TEXT,category TEXT,state TEXT DEFAULT "pending",error TEXT DEFAULT "")'); self.db.execute('CREATE TABLE IF NOT EXISTS leads(id TEXT PRIMARY KEY,data TEXT)'); self.db.commit()
 def configure_searches(self,urls,cat,restart=False):
  seeds=sorted(set(search_start(u) for u in urls if u.strip()))
  self.db.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)')
  active=self.db.execute('SELECT value FROM settings WHERE key="active_seeds"').fetchone()
  if not seeds:
   if restart:raise ValueError('Paste a search URL to restart.')
   return False
  if active:old=json.loads(active[0])
  else:
   old=sorted(set(search_start(r[0]) for r in self.db.execute('SELECT url FROM jobs WHERE kind="listing"')))
  changed=bool(old and seeds!=old)
  if restart or changed:
   self.db.execute('CREATE TABLE IF NOT EXISTS archived_jobs AS SELECT *, 0 AS archived_at FROM jobs WHERE 0')
   self.db.execute("INSERT INTO archived_jobs SELECT *, strftime('%s','now') FROM jobs")
   self.db.execute('DELETE FROM jobs')
  self.db.execute('INSERT OR REPLACE INTO settings VALUES("active_seeds",?)',(json.dumps(seeds),))
  for u in seeds:self.db.execute('INSERT OR IGNORE INTO jobs(url,kind,category) VALUES(?,"listing",?)',(u,cat))
  self.db.commit();return restart or changed
 def add(self,u,kind,cat):
  u=canonical(u)
  if u: self.db.execute('INSERT OR IGNORE INTO jobs(url,kind,category) VALUES(?,?,?)',(u,kind,cat)); self.db.commit()
 def save(self,row):
  old=self.db.execute('SELECT data FROM leads WHERE id=?',(row['profile_url'],)).fetchone()
  if old:
   prev=json.loads(old[0]); prev.update({k:v for k,v in row.items() if v}); row=prev
  self.db.execute('INSERT OR REPLACE INTO leads VALUES(?,?)',(row['profile_url'],json.dumps(row))); self.db.commit()
 def ingest(self,s,url,cat,live=False):
  rows,pages,root=parse(s,url,cat)
  for row in rows: self.save(row); self.add(row['profile_url'],'profile',cat)
  for p in pages: self.add(p,'listing',cat)
  return len(rows),root
 def retry_missing(self):
  count=0
  for ident,raw in self.db.execute('SELECT id,data FROM leads').fetchall():
   row=json.loads(raw)
   if not row.get('phone','').strip():
    self.add(ident,'profile',row.get('category',''))
    self.db.execute('UPDATE jobs SET state="pending",error="" WHERE url=?',(ident,));count+=1
  self.db.commit();return count
 def export(self,folder):
  fields=['company','phone','contact_name','contact_title','address','category','profile_url','source_url','status']
  rows=[json.loads(x[0]) for x in self.db.execute('SELECT data FROM leads ORDER BY id')]
  def safe(v):
   v=str(v or ''); return "'"+v if v.startswith(('=','+','-','@')) else v
  p=Path(folder); p.mkdir(exist_ok=True)
  with (p/'BlueBook_Leads.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.writer(f); w.writerow(fields); w.writerows([[safe(r.get(k,'')) for k in fields] for r in rows])
  try:
   from openpyxl import Workbook
   wb=Workbook(); ws=wb.active; ws.title='Leads'; ws.append(fields)
   for r in rows: ws.append([safe(r.get(k,'')) for k in fields])
   ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
   for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=28
   wb.save(p/'BlueBook_Leads.xlsx')
  except ImportError: pass
  return len(rows)
