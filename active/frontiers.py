# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest articles from Frontiers-journal
# FS 2018-08-28

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

timestamp = time.strftime("%03j-%H%M", time.localtime())
publisher = 'Frontiers'
typecode = 'P'
jnlfilename = 'frontiers.' + timestamp

sectiontofc = {'Astrobiology' : 'a', 'Astrochemistry' : 'a',
               'Exoplanets' : 'a', 'Astrostatistics' : 'a',
               'Extragalactic Astronomy' : 'a', 'Fundamental Astronomy' : 'a',
               'Space Physics' : 'a', 'Space Robotics' : 'a',
               'High-Energy and Astroparticle Physics' : 'a',
               'Planetary Science' : 'a', 'Stellar and Solar Physics' : 'a',
               'Astronomical Instrumentation' : 'ai',
               'Radiation Detectors and Imaging' : 'i',
               'Cosmology' : 'ag',
               'Condensed Matter Physics' : 'f',
               'Machine Learning and Artificial Intelligence' : 'c',
               'Mathematical and Statistical Physics' : 'm'}

urls = sys.argv[1:]
recs = []
i = 0
for artlink in urls:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(urls), artlink)
    if artlink in ['http://click.engage.frontiersin.com/?qs=42b61da43a3f9df6013a23b68436a54baa8c80ffee48007a24c58c48dea197f28e8e542608b09cd5f247e97e276ce0ad2dc2d41a82d633a97db80e0b25f249be',
                   'http://click.engage.frontiersin.com/?qs=f38f1870c56dcbfecc918de16e443951cd63dd13638046942de37046a6b277e1b668fc558b74e4d8fce61d9c60b0fbbaa011c26e0b58e0b1aed51711d07b43af',
                   'http://click.engage.frontiersin.com/?qs=7924d9eced8ace4bc1fe79b5d27da08c4edb5ac2f674162f35a53feaecc1801271ce07c9c7c074668b8e64e1ccf21c2135d1cb211cc57e34a6b9cffc865f7d03',
                   'http://click.engage.frontiersin.com/?qs=f38f1870c56dcbfecc918de16e443951cd63dd13638046942de37046a6b277e135eed14992b8c3c7d2122930241cf225aa6a324ac73c3f57366a06bbc2fdd4a1',
                   'http://click.engage.frontiersin.com/?qs=f38f1870c56dcbfe8541a1a57ac950e6a60498ebc55375cffafff4fd3132555d20394944b66337553cda0df56ba94f01d305afd60124df417ca75062ffee02cd',
                   'http://click.engage.frontiersin.com/?qs=f38f1870c56dcbfe8541a1a57ac950e6a60498ebc55375cffafff4fd3132555dc2671c4873b888b1088098d8c958d81929a3a95368064553cb63c83832025ef4']:
        continue
    rec = {'tc' : 'P', 'autaff' : [], 'refs' : [], 'note' : []}
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (artlink)
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink), features="lxml")
    autaff = False
    try:
        artpage.head.find_all('meta')
    except:
        continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #volume
            if meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            #journal
            elif meta['name'] == 'citation_journal_title':
                if meta['content'] == 'Frontiers in Astronomy and Space Sciences':
                    rec['jnl'] = 'Front.Astron.Space Sci.'
                elif meta['content'] == 'Frontiers in Physics':
                    rec['jnl'] = 'Front.in Phys.'
                elif meta['content'] == 'Frontiers in Artificial Intelligence':
                    rec['jnl'] = 'Front.Artif.Intell.'
                elif meta['content'] == 'Frontiers in Big Data':
                    rec['jnl'] = 'Front.Big Data'
                else:
                    print 'do not know journal "%s"!' % (meta['content'])
                    sys.exit(0)
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #pages
            elif meta['name'] == 'citation_pages':
                rec['p1'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split(' *; *', meta['content'])
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #date
            elif meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
            #year
            elif meta['name'] == 'citation_date':
                rec['year'] = meta['content']
            #autaff
            elif meta['name'] == 'citation_author':
                if autaff:
                    rec['autaff'].append(autaff)
                autaff = [ meta['content'] ]
            elif meta['name'] == 'citation_author_institution':
                autaff.append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                autaff.append('ORCID:%s' % (orcid))
                orcidsfound = True
            elif meta['name'] == 'citation_author_email':
                if meta['content']:
                    email = meta['content']
                    autaff.append('EMAIL:%s' % (email))
    if not 'doi' in rec.keys():
        continue
    if autaff:
        rec['autaff'].append(autaff)
    #license
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['license'] = {'url' : a['href']}
    #FFT
    if not 'FFT' in rec.keys():
        rec['FFT'] = 'https://www.frontiersin.org/articles/%s/pdf' % (rec['doi'])
    #section
    for a in artpage.body.find_all('a', attrs = {'data-test-id' : 'section-link'}):
        section = a.text.strip()
        if section in sectiontofc.keys():
            if 'fc' in rec.keys():
                for fc in sectiontofc[section]:
                    if not fc in rec['fc']:
                        rec['fc'] += fc
            else:
                rec['fc'] = sectiontofc[section]
        else:
            rec['note'].append(section)
    #references
    for div in artpage.body.find_all('div', attrs = {'class' : 'References'}):
        for a in div.find_all('a'):
            a.replace_with('')
        rec['refs'].append([('x', div.text.strip())])
    ### meta tags not well formatted or filled
    #date
    for div in artpage.body.find_all('div', attrs = {'class' : 'article-header-container'}):
        if not 'date' in rec.keys() or rec['date'] == '0001/01/01':            
            for div2 in div.find_all('div', attrs = {'class' : 'header-bar-three'}):
                div2t = re.sub('[\n\r\t]', ' ', div2.text.strip())
                if re.search(' [12]\d\d\d', div2t):
                    rec['date'] = re.sub('.*, (.*?[12]\d\d\d).*', r'\1', div2t)
    #pubnote
    for div in artpage.body.find_all('div', attrs = {'class' : 'AbstractSummary'}):
        for p in div.find_all('p'):
            for span in p.find_all('span'):
                if re.search('Citation:', span.text):
                    pt = p.text.strip()
                    if re.search('Front.* (\d+:\d+)\. doi', pt):
                        rec['vol'] = re.sub('.*Front.* (\d+):\d+\. doi.*', r'\1', pt)
                        rec['p1'] = re.sub('.*Front.* \d+:(\d+)\. doi.*', r'\1', pt)        
    print '   ', rec.keys()
    recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
