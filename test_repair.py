import unittest,tempfile,json
from pathlib import Path
from core import Tree,phones,profile_data,Store
class RepairTests(unittest.TestCase):
 def test_meta_and_labels(self):
  r=Tree('<meta itemprop="telephone" content="(213) 555-1234"><div>Phone: 310.555.4567 ext 12</div><div class="fax">Fax: 818-555-7777</div>').root
  self.assertEqual(phones(r),'2135551234; 3105554567 ext 12')
 def test_jsonld_match(self):
  content='<script type="application/ld+json">[{"name":"Acme","telephone":"213-555-1234"},{"name":"Other","telephone":"818-555-7777"}]</script>'
  row=profile_data(content,{'company':'Acme','phone':''})
  self.assertEqual(row['phone'],'2135551234')
 def test_keep_name_and_phone(self):
  row=profile_data('<main>No number</main>',{'company':'Acme','phone':'2135551234'})
  self.assertEqual(row['company'],'Acme');self.assertEqual(row['phone'],'2135551234')
 def test_scoped(self):
  content='<footer><a href="tel:8185557777">Other</a></footer><main><p>Phone: 213-555-1234</p></main>'
  self.assertEqual(profile_data(content,{'company':'Acme','phone':''})['phone'],'2135551234')
 def test_retry_only_missing(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'s.db')
   for i,phone in [(1,'2135551234'),(2,'')]:
    u=f'https://www.thebluebook.com/iProView/{i}'
    s.save({'profile_url':u,'company':str(i),'phone':phone});s.add(u,'profile','GC')
   s.db.execute('update jobs set state="done"');s.db.commit();self.assertEqual(s.retry_missing(),1)
   self.assertEqual(s.db.execute('select count(*) from jobs where state="done"').fetchone()[0],1)
if __name__=='__main__':unittest.main()
