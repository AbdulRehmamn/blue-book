import unittest,tempfile
from pathlib import Path
from core import Store,parse,canonical,phones,Tree
class Tests(unittest.TestCase):
 def test_pagination_scope(self):
  h='<a href="/search.html?region=3&class=2200&page=2">2</a><a href="/search.html?region=4&class=2200&page=2">Other</a>'
  self.assertEqual(len(parse(h,'https://www.thebluebook.com/search.html?region=3&class=2200')[1]),1)
 def test_dedupe_resume(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'p.db');u='https://www.thebluebook.com/search.html?region=3&class=2200'
   s.add(u,'listing','GC');s.add(u,'listing','GC')
   self.assertEqual(s.db.execute('select count(*) from jobs').fetchone()[0],1)
   s.db.execute('update jobs set state="done"');s.db.commit();s.db.close()
   s=Store(Path(d)/'p.db');self.assertEqual(s.db.execute('select state from jobs').fetchone()[0],'done');s.db.close()
 def test_phone_scope(self):
  r=Tree('<a href="tel:8887201710">Support</a><span itemprop="telephone">(714) 538-4709</span><p>626-380-7751</p>').root
  self.assertEqual(phones(r),'7145384709')
if __name__=='__main__':unittest.main()
