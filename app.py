from pathlib import Path
import threading, queue, time, json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from core import Store, canonical, first, phones, profile_data
ROOT=Path(__file__).resolve().parent
DB=ROOT/'progress.sqlite3'
class App:
 def __init__(self,w):
  self.w=w; w.title('Blue Book • Pacific Lead Collector'); w.geometry('1050x700'); self.stop=threading.Event(); self.events=queue.Queue(); self.busy=False; self.verified=threading.Event()
  ttk.Label(w,text='Blue Book Lead Collector',font=('Segoe UI',20,'bold')).pack(pady=12)
  ttk.Label(w,text='General contractors • Subcontractors • Owners / Developers | Local saved progress').pack()
  ttk.Label(w,text='Paste actual Blue Book search URLs (one per line). All pages linked by each search are queued.').pack(pady=8)
  self.urls=tk.Text(w,height=6); self.urls.pack(fill='x',padx=15); self.urls.insert('1.0','https://www.thebluebook.com/search.html?region=3&class=2200')
  self.cat=tk.StringVar(value='General contractors'); ttk.Combobox(w,textvariable=self.cat,values=['General contractors','Subcontractors / all trades','Owners / Developers'],state='readonly').pack(pady=6)
  b=ttk.Frame(w); b.pack()
  for text,cmd in [('Restart URL from page 1',self.restart),('Start / Resume',self.start),('Stop & save',self.stop.set),('Import saved HTML',self.imp),('Export Excel / CSV',self.export)]: ttk.Button(b,text=text,command=cmd).pack(side='left',padx=3)
  actions=ttk.Frame(w); actions.pack(pady=5)
  ttk.Button(actions,text='Edit company / contact name',command=self.edit_names).pack(side='left',padx=5)
  ttk.Button(actions,text='Retry missing phones',command=self.retry_missing).pack(side='left',padx=5)
  ttk.Button(actions,text='Verification completed — Continue',command=self.verified.set).pack(side='left',padx=5)
  ttk.Label(w,text='Pacific scope: add searches for each relevant Blue Book region and category. See COVERAGE.md.\nOnly the supplied Los Angeles general-contractor search is preconfigured.').pack(pady=10)
  self.log=tk.Text(w,height=17,state='disabled'); self.log.pack(fill='both',expand=True,padx=15,pady=8)
  w.protocol('WM_DELETE_WINDOW',self.close); self.poll(); self.say('Progress is saved in progress.sqlite3. Reopen this folder and press Start / Resume.')
 def say(self,t): self.events.put(t)
 def poll(self):
  while not self.events.empty():
   t=self.events.get(); self.log.configure(state='normal'); self.log.insert('end',t+'\n'); self.log.see('end'); self.log.configure(state='disabled')
  self.w.after(200,self.poll)
 def add(self,restart=False):
  s=Store(DB)
  try:
   changed=s.configure_searches(self.urls.get('1.0','end').splitlines(),self.cat.get(),restart)
   self.say('Started a new queue from page 1; previous jobs archived and leads preserved.' if changed else 'Resuming saved queue; completed URLs stay skipped.')
   return True
  except ValueError as e:messagebox.showerror('Search URL',str(e));return False
  finally:s.db.close()
 def restart(self):
  if self.busy:return messagebox.showinfo('Running','Click Stop & save and wait for the saved message first.')
  if self.add(restart=True):self.launch()
 def imp(self):
  if self.busy: return messagebox.showinfo('Running','Stop the collection before importing.')
  files=filedialog.askopenfilenames(filetypes=[('Saved HTML','*.html *.htm')]); s=Store(DB)
  for f in files:
   # Saved pages contain their own canonical URL, if available.
   from core import Tree
   content=Path(f).read_text(encoding='utf-8',errors='replace'); root=Tree(content).root
   n=first(root,lambda n:n.tag=='link' and n.a.get('rel')=='canonical')
   u=n.a['href'] if n else self.urls.get('1.0','end').strip().splitlines()[0]
   count,_=s.ingest(content,u,self.cat.get()); self.say(f'Imported {count} listings from {Path(f).name}')
  s.export(ROOT/'exports'); s.db.close()
 def export(self):
  try:
   s=Store(DB); n=s.export(ROOT/'exports'); s.db.close(); self.say(f'Exported {n} companies to the exports folder.')
  except Exception as e: self.say('Export error (close Excel and retry): '+str(e))
 def start(self):
  if self.busy:return
  if self.add():self.launch()
 def launch(self):
  self.stop.clear(); self.busy=True; threading.Thread(target=self.run,daemon=True).start()
 def edit_names(self):
  if self.busy:return messagebox.showinfo('Running','Stop & save before editing names.')
  u=simpledialog.askstring('Find company','Paste its exact profile_url from the export:')
  if not u:return
  s=Store(DB)
  try:
   record=s.db.execute('SELECT data FROM leads WHERE id=?',(canonical(u.strip()),)).fetchone()
   if not record:return messagebox.showerror('Not found','No saved company matches that profile URL.')
   row=json.loads(record[0])
   for key,label in [('company','Company name'),('contact_name','Public contact / owner name'),('contact_title','Contact title (Owner only if verified)')]:
    val=simpledialog.askstring('Edit name',label,initialvalue=row.get(key,''))
    if val is None:return
    if key=='company' and not val.strip():return messagebox.showerror('Name required','Company name cannot be blank.')
    row[key]=val.strip()
   s.db.execute('UPDATE leads SET data=? WHERE id=?',(json.dumps(row),row['profile_url']));s.db.commit();s.export(ROOT/'exports');self.say('Names updated and exported.')
  finally:s.db.close()
 def retry_missing(self):
  if self.busy:return messagebox.showinfo('Running','Stop first, then retry missing phones.')
  s=Store(DB);n=s.retry_missing();s.db.close();self.say(f'Queued {n} profiles without phones. Press Start / Resume.')
 def check_access(self,page,status):
  text=page.locator('body').inner_text().lower()
  challenge=any(x in text for x in ['verify you are human','verify that you are human','robot verification','checking your browser','performing security verification','just a moment'])
  if challenge:
   self.verified.clear();self.say('Verification required: complete it yourself in the OPEN browser, then click Verification completed — Continue. Stop & save is also available.')
   while not self.stop.is_set() and not self.verified.wait(0.25):pass
   if self.stop.is_set():raise RuntimeError('Stopped with current URL pending.')
   text=page.locator('body').inner_text().lower()
   if any(x in text for x in ['verify you are human','verify that you are human','robot verification','checking your browser','performing security verification','just a moment','request blocked','access denied']):raise RuntimeError('Verification is still blocking access. Stopped without retrying.')
  elif status>=400 or any(x in text for x in ['request blocked','access denied']):
   raise RuntimeError(f'Access error {status}. Saved progress; no automatic bypass or repeated retries.')
 def run(self):
  s=Store(DB)
  try:
   from playwright.sync_api import sync_playwright
   with sync_playwright() as pw:
    browser=pw.chromium.launch_persistent_context(str(ROOT/'browser_session'),headless=False); page=browser.pages[0] if browser.pages else browser.new_page()
    while not self.stop.is_set():
     job=s.db.execute('SELECT url,kind,category FROM jobs WHERE state="pending" ORDER BY CASE kind WHEN "profile" THEN 0 ELSE 1 END,rowid LIMIT 1').fetchone()
     if not job: self.say('Queue complete. Use Restart URL from page 1 to run this search again, or Retry missing phones then Start / Resume.'); break
     u,kind,cat=job; self.say('Reading '+u)
     try:
      response=page.goto(u,wait_until='domcontentloaded',timeout=45000)
      page.wait_for_timeout(2000)
      self.check_access(page,response.status if response else 200)
      content=page.content()
      if kind=='listing':
       count,root=s.ingest(content,u,cat)
       if not count: raise RuntimeError('No listing cards found. Page may require login or its layout has changed; not marked complete.')
       self.say(f'Saved {count} listings; discovered pagination and profile links.')
      else:
       row=s.db.execute('SELECT data FROM leads WHERE id=?',(u,)).fetchone()
       if not row: raise RuntimeError('Missing source listing')
       row=profile_data(content,json.loads(row[0]))
       s.save(row)
      s.db.execute('UPDATE jobs SET state="done",error="" WHERE url=?',(u,)); s.db.commit()
     except Exception as e:
      s.db.execute('UPDATE jobs SET error=? WHERE url=?',(str(e),u)); s.db.commit(); self.say(str(e)); break
     if self.stop.wait(4): break
    browser.close()
  except Exception as e:self.say('Stopped: '+str(e))
  finally:
   try:self.say(f'Saved/exported {s.export(ROOT/"exports")} companies. Resume skips completed URLs.')
   except Exception as e:self.say('Database saved; export failed: '+str(e))
   s.db.close(); self.busy=False
 def close(self):
  if self.busy:self.stop.set(); messagebox.showinfo('Saving','Stop requested. Wait for the export message, then close.'); return
  self.w.destroy()
if __name__=='__main__':
 w=tk.Tk(); App(w); w.mainloop()
