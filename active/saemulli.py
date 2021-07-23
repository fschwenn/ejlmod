# -*- coding: UTF-8 -*-
#program to harvest "New Physics: Sae Mulli"
# FS 2017-08-18


import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'Korean physical Society'
tc = 'P'
vol = sys.argv[1]
issue = sys.argv[2]

jnlname = 'New Phys.Sae Mulli'
urltrunk = 'http://www.npsm-kps.org'

jnlfilename = "npsm%s.%s" % (vol, issue)
toclink = "%s/list.html?page=1&sort=&scale=500&all_k=&s_t=&s_a=&s_k=&s_v=%s&s_n=%s&spage=&pn=search&year=" % (urltrunk, vol, issue)
toclink = "%s/journal/list.html?pn=vol&TG=vol&sm=&s_v=%s&s_n=%s&scale=500" % (urltrunk, vol, issue)

print "get table of content... from %s" % (toclink)

try:
    tocpage = BeautifulSoup(urllib2.urlopen(toclink), features="lxml")
except:
    print '%s not found' % (toclink)
    sys.exit(0)


recs = []
recc = re.compile('http.*creativecommons.org')
repacs = re.compile('PACS numbers:? *')

for h4 in tocpage.body.find_all('h4'):
    rec = {'jnl' : jnlname, 'tc' : tc, 'issue' : issue, 'note' : [], 
           'auts' : [], 'aff' : [], 'keyw' : [], 'vol' : vol}
    for a in h4.find_all('a'):
        artlink = '%s/%s' % (urltrunk, a['href'])
        rec['tit'] = a.text.strip()
        time.sleep(4)
        try:
            artpage = BeautifulSoup(urllib2.urlopen(artlink))
        except:
            print '%s not found' % (artlink)
            sys.exit(0)
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                if meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                elif meta['name'] == 'citation_pdf_url':
                    rec['fulltext'] = meta['content']
                elif meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content']
                elif meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content']
                elif meta['name'] == 'citation_keywords':
                    rec['keyw'].append(meta['content'])
                elif meta['name'] == 'citation_online_date':
                    rec['date'] = meta['content']
        #check for licence
        for a in artpage.body.find_all('a'):
            if a.has_attr('href'):
                if recc.search(a['href']):
                    rec['licence'] = {'url' : a['href']}
        #abstract
        for dd in artpage.body.find_all('div', attrs = {'class' : 'go_section'}):
            rec['abs'] = re.sub('Keywords:.*', '', dd.text.strip())
        #authors
        for diva in artpage.body.find_all('div', attrs = {'class' : 'origin_section02'}):
            ps = diva.find_all('p')
            for sup in ps[0].find_all('sup'):
                aff = ''
                for supp in re.split(',', sup.text.strip()):
                    aff += ', =Aff' + supp
                sup.replace_with(aff)
            for author in re.split(' *, *', ps[0].text.strip()):
                author = re.sub('\*', '', author)
                if re.search('=Aff', author):
                    rec['auts'].append(author)
                else:
                    rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', author))
            ps[0].decompose()
            print 'XXX auts', rec['auts']
        #affiliations
        for diva in artpage.body.find_all('div', attrs = {'class' : 'inner_content'}):
            for h2 in diva.find_all('h2'):
                h2.replace_with('XXXX')
            for sup in diva.find_all('sup'):
                aff = ';;; Aff%s= ' % (sup.text.strip())
                sup.replace_with(aff)
            divat = re.sub('Correspondence to:.*', '', re.sub('[\n\t\r]', ' ', diva.text.strip()))
            divat = re.sub('.*XXXX', '', divat)
            divat = re.sub('Abstract *Go to Abstract.*', '', divat)
            print divat
            divat = re.sub('Received.*', '', divat)
            
            for aff in re.split(';;;', divat):
                if len(aff) > 6:
                    rec['aff'].append(aff.strip())
            print 'XXXaff', rec['aff']
        recs.append(rec)
        print rec['doi'], rec.keys()
    
    
#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
