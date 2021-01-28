# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest International Press Boston
# FS 2012-06-01

import codecs
import os
import ejlmod2
import re
import sys
import unicodedata
import string
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

tmpdir = '/tmp'
printer = "l00ps5 "
def tfstrip(x): return x.strip()

publisher = 'International Press'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]

jnlfilename = jnl+vol+'.'+isu

if   (jnl == 'atmp'): 
    jnlname = 'Adv.Theor.Math.Phys.'
    issn = '1095-0761'
    url = "http://www.intlpress.com/%s/%s-issue_%s_%s.php" % (jnl.upper(),jnl.upper(),vol,isu)
elif (jnl == 'amsa'):
    jnlname = 'Ann.Math.Sci.Appl.'
    issn = '2380-288X'
    url = "http://www.intlpress.com/%s/%s-vol-%s.php" % (jnl.upper(),jnl.upper(),vol)
elif (jnl == 'cntp'):
    jnlname = 'Commun.Num.Theor.Phys.'
    issn = '1931-4523'
    url = "http://www.intlpress.com/%s/%s-vol-%s.php" % (jnl.upper(),jnl.upper(),vol)
    url = 'https://www.intlpress.com/site/pub/pages/journals/items/%s/content/vols/%04i/%04i/index.php' % (jnl,int(vol),int(re.sub('\D.*', '', isu)))
elif (jnl == 'ajm'):
    jnlname = 'Asian J.Math.'
    issn = '1093-6106'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
    url = 'https://www.intlpress.com/site/pub/pages/journals/items/%s/content/vols/%04i/%04i/index.php' % (jnl,int(vol),int(re.sub('\D.*', '', isu)))
elif (jnl == 'jdg'):
    jnlname = 'J.Diff.Geom.'
    issn = '0022-040X'
    year = str(int(vol) / 3 + 1982)
    url = "http://www.intlpress.com/%s/%s/%s-v%s.php" % (jnl.upper(),year,jnl.upper(),vol)
elif (jnl == 'cag'):
    jnlname = 'Commun.Anal.Geom.'
    issn = '1019-8385'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
    url = 'https://www.intlpress.com/site/pub/pages/journals/items/%s/content/vols/%04i/%04i/index.php' % (jnl,int(vol),int(re.sub('\D.*', '', isu)))
elif (jnl == 'cjm'): #fall 2012
    jnlname = 'Cambridge J.Math.'
    issn = '2168-0930'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
elif (jnl == 'cms'):
    jnlname = 'Commun.Math.Sci.'
    issn = '1539-6746'
    year = str(int(vol)+2002)
    url = "http://www.intlpress.com/%s/%s/issue%s-%s" % (jnl.upper(),year,vol,isu)
elif (jnl == 'jsg'):
    jnlname = 'J.Sympl.Geom.'
    issn = '1527-5256'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
elif (jnl == 'mrl'): # fulltext via http://www.intlpress.com/_newsite/site/pub/files/_fulltext/journals/mrl/
    jnlname = 'Math.Res.Lett.'
    issn = '1073-2780'
    url = "http://www.intlpress.com/site/pub/pages/journals/items/%s/content/vols/00%s/000%s/index.php" % (jnl,vol,isu)
elif (jnl == 'pamq'):
    jnlname = 'Pure Appl.Math.Quart.'
    issn = '1558-8599'
    url = 'https://www.intlpress.com/site/pub/pages/journals/items/%s/content/vols/%04i/%04i/index.php' % (jnl,int(vol),int(re.sub('\D.*', '', isu)))
elif (jnl == 'iccm'):
    jnlname = 'ICCM Not.'
    issn = '2326-4810'
    url = 'https://www.intlpress.com/site/pub/pages/journals/items/%s/content/vols/%04i/%04i/index.php' % (jnl,int(vol),int(re.sub('\D.*', '', isu)))
if len(vol) == 1: vol = '0'+vol
#url = "http://intlpress.com/site/pub/pages/journals/items/%s/content/vols/00%s/000%s/body.html" % (jnl,vol,isu)


print "get table of content of %s%s.%s ..." %(jnlname,vol,isu)
print "lynx -source \"%s\"" % (url)
tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(url))


recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'list_item'}):
    rec = {'vol' : vol, 'jnl' : jnlname, 'tc' : 'P', 'issue' : isu,
           'autaff' : [], 'note' : [], 'abs' : ''}
    for a in div.find_all('a'):
        rec['artlink'] = 'http://www.intlpress.com/' + a['href']
        print '.', rec['artlink']
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                if meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content']
                elif meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content']
                elif meta['name'] == 'citation_year':
                    rec['year'] = meta['content']
                elif meta['name'] == 'citation_doi':
                    if meta['content']:
                        rec['doi'] = meta['content']
                    else:
                        rec['link'] = rec['artlink']
                        rec['doi'] = '20.2000/' + re.sub('\W', '',  rec['artlink'][10:])
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']                
                elif 'citation_author' == meta['name']:
                    aut = meta['content']
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
                    if re.search(',', aut):
                        rec['autaff'].append([aut])
                    else:
                        rec['autaff'].append([re.sub('(.*) (.*)', r'\2, \1', aut)])
                elif 'citation_author_institution' == meta['name']:
                    if len(rec['autaff']) > 0:
                        rec['autaff'][-1].append(re.sub('^\d*', '', meta['content'])) 
                elif meta['name'] == 'citation_author_email':
                    email = meta['content']
                    rec['autaff'][-1].append('EMAIL:%s' % (email)) 
                elif meta['name'] == 'citation_pdf_url':
                    if not rec.has_key('doi'):
                        rec['pdf'] = meta['content']
        for p in artpage.body.find_all('p', attrs = {'class' : 'contentitem_abstract'}):
            rec['abs'] += p.text
        for p in artpage.body.find_all('p', attrs = {'class' : 'contentitem_keywords'}):
            rec['keyw'] = re.split(', ', p.text)
        recs.append(rec)
        print '   ', rec.keys()


xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()

#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
