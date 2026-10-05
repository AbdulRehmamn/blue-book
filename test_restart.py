import unittest,tempfile
from pathlib import Path
from core import Store
class RestartTests(unittest.TestCase):
 def test_restart_preserves_leads_and_starts_page_one(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db');u='https://www.thebluebook.com/search.html?region=3&class=2200&page=15'
   s.add(u,'listing','GC');s.save({'profile_url':'https://www.thebluebook.com/iProView/123','company':'Test Co','phone':'2135551234'})
   s.configure_searches([u],'GC',True)
   jobs=s.db.execute('select url,state from jobs').fetchall();self.assertEqual(len(jobs),1);self.assertNotIn('page=',jobs[0][0]);self.assertEqual(jobs[0][1],'pending')
   self.assertEqual(s.db.execute('select count(*) from leads').fetchone()[0],1)
   self.assertEqual(s.db.execute('select count(*) from archived_jobs').fetchone()[0],1)
 def test_resume_and_switch(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db');u='https://www.thebluebook.com/search.html?region=3&class=2200';v='https://www.thebluebook.com/search.html?region=4&class=2200'
   s.configure_searches([u],'GC');s.db.execute('update jobs set state="done"');s.db.commit()
   self.assertFalse(s.configure_searches([u],'GC'));self.assertEqual(s.db.execute('select state from jobs').fetchone()[0],'done')
   self.assertTrue(s.configure_searches([v],'GC'));self.assertIn('region=4',s.db.execute('select url from jobs').fetchone()[0])
if __name__=='__main__':unittest.main()
