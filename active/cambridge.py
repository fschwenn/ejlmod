# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Cambridge-journals
# FS 2015-02-12


import sys
import os
import ejlmod2
import re
import urllib2,cookielib
import urlparse
import codecs
import time
from bs4 import BeautifulSoup
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Cambridge University Press'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

tc = 'P'
jid =  sys.argv[1]
vol = sys.argv[2]
jnlfilename = 'cambridge'+jid + vol
if len(sys.argv) > 3:
    iss = sys.argv[3]
    jnlfilename += '.' + iss
else:
    jnlfilename += '.' + stampoftoday

if len(sys.argv) > 4:
    jnlfilename += '.' + sys.argv[4]
    tc = 'C'
if len(sys.argv) > 5:
    explicittoclink = sys.argv[5]

if jid == 'IAU':
    jnlname = 'IAU Symp.'
elif jid == 'PSP':
    jnlname = 'Math.Proc.Cambridge Phil.Soc.'
elif jid == 'FMS':
    jnlname = 'Forum Math.Sigma'
elif jid == 'LPB':
    jnlname = 'Laser Part.Beams'
elif jid == 'JAZ':
    jnlname = 'J.Austral.Math.Soc.'
elif jid == 'PAS':
    jnlname = 'Publ.Astron.Soc.Austral.'
elif jid == 'PLA':
    jnlname = 'J.Plasma Phys.'
elif jid == 'IJA':
    jnlname = 'Int.J.Astrobiol.'
elif jid == 'GMJ':
    jnlname = 'Glasgow Math.J.'    
#--
elif jid == 'BAZ':
    jnlname = 'Bull.Austral.Math.Soc.'
elif jid == 'CPH':
    jnlname = 'Commun.Comput.Phys.'
elif jid == 'COM':
    jnlname = 'Compos.Math.'
elif jid == 'FMP':
    jnlname = 'Forum Math.Pi'
elif jid == 'MTK':
    jnlname = 'Mathematika'
elif jid == 'JOG':
    jnlname = 'J.Glaciol.'
elif jid == 'CJM':
    jnlname = 'Can.J.Math.'
#
elif jid == 'SIC':
    jnlname = 'Sci.Context'

if len(sys.argv) > 5:
    toclink = explicittoclink
else:
    toclink = 'http://journals.cambridge.org/action/displayIssue?jid=%s&volumeId=%s' % (jid, vol)
    if len(sys.argv) > 3:
        toclink += '&issueId=%s' % (iss)
        print toclink


#toclink = "https://www.cambridge.org/core/journals/compositio-mathematica/issue/9AB804B5DBC553D5DD4916D1B7BDAA72"

        
if not os.path.isfile('/tmp/%s.0.toc' % (jnlfilename)):
    os.system('wget -O /tmp/%s.0.toc "%s"' % (jnlfilename, toclink))
tocf = open('/tmp/%s.0.toc' % (jnlfilename), 'r')
toc = BeautifulSoup(''.join(tocf.readlines()))
tocf.close()

#check number of toc-pages
for meta in toc.head.find_all('meta', attrs = {'property' : 'og:url'}):
    baseurl = 'https://www.cambridge.org' + meta['content']
    numpages = 1
    for div in toc.body.find_all('div', attrs = {'class' : 'results'}):
        for p in div.find_all('p', attrs = {'class' : 'paragraph_05'}):
            ptext = p.text.strip()
            if re.search('age \d+ of \d+', ptext):
                numpages = int(re.sub('.* of (\d+).*', r'\1', ptext))
                print 'check %i pages' % (numpages)

note = ''
recs = []
#first run through TOC to get DOIs
for i in range(numpages):
    toclink = '%s?pageNum=%i' % (baseurl, i+1)
    print ' . ', toclink
    if not os.path.isfile('/tmp/%s.%i.toc' % (jnlfilename, i)):
        os.system('wget -O /tmp/%s.%i.toc "%s"' % (jnlfilename, i, toclink))
    tocf = open('/tmp/%s.%i.toc' % (jnlfilename, i), 'r')
    toc = BeautifulSoup(''.join(tocf.readlines()))
    tocf.close()
    for div in toc.body.find_all('div'):
        if div.has_attr('class') and 'columns' in div['class']:
            if 'large-12' in div['class'] and 'margin-top' in div['class']:
                for child in div.children:
                    rec = {'refs' : [], 'tc' : tc,
                           'autaff' : [], 'keyw' : [], 'jnl' : jnlname}
                    if len(sys.argv) > 3:
                        rec['issue'] = iss
                    try:
                        child.name
                    except:
                        continue
                    if child.name == 'h4':
                        note = child.text.strip()
                    elif child.name == 'div':
                        for a in child.find_all('a', attrs = {'class' : 'url doi'}):
                            rec['artlink2'] = a['href']
                            rec['note'] = [ note ]
                            rec['doi'] = re.sub('.*doi.org.', '', a['href'])
                            if rec['doi'] in ['10.4208/cicp.060515.161115b', 
                                              '10.1017/S0022377818000430',
                                              '10.1112/S0025579318000232',
                                              '10.1112/S0025579318000244',
                                              '10.1112/S0025579318000256']:
                                continue
                            if not note in ['Front Cover (OFC, IFC) and matter', 
                                        'Back Cover (OBC, IBC) and matter']:
                                recs.append(rec)
                                print rec['doi'], rec['note']
                        #real article link
                        for a2 in child.find_all('a', attrs = {'class' : 'part-link'}):
                            rec['artlink'] = 'https://www.cambridge.org' + a2['href']
                            if not 'doi' in rec.keys():
                                rec['note'] = [ note ]
                                if not note in ['Front Cover (OFC, IFC) and matter', 
                                                'Back Cover (OBC, IBC) and matter']:
                                    recs.append(rec)
                                    print '?', rec['note']


#2nd run to get details for individual articles
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
i = 0
for rec in recs:    
    i += 1 
    req = urllib2.Request(rec['artlink'], headers=hdr)
    print rec['artlink']
    try:
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(10)
    except:
        if 'artlink2' in rec.keys():
            print 'wait 3 minutes befor trying %s instead of %s' % (rec['artlink2'], rec['artlink'])
            time.sleep(180)
            req = urllib2.Request(rec['artlink2'], headers=hdr)
        else:
            print 'wait 3 minutes befor trying  again'
            time.sleep(180)
            req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(2)
    try:
        print '------{ %s }------{ %i/%i }------' % (rec['doi'], i, len(recs))
    except:
        print '------{ %i/%i }------' % (i, len(recs))
    for meta in artpage.head.find_all('meta'):
        if meta.attrs.has_key('name'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #pubnote
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_volume':
                if jid == 'IAU':
                    rec['vol'] = vol
                else:
                    rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                if not jid == 'IAU':
                    rec['issue'] = meta['content']
            elif meta['name'] == 'citation_publication_date':
                rec['year'] = meta['content'][:4]
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content'].title()])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            elif meta['name'] == 'citation_author_email':
                email = meta['content']
                rec['autaff'][-1].append('EMAIL:%s' % (email))
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                rec['autaff'][-1].append('ORCID:%s' % (orcid))
            #date
            elif meta['name'] == 'citation_online_date':
                 rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                 rec['keyw'] += re.split(' *; *', meta['content'])
    #CNUM
    if len(sys.argv) > 4:
        rec['cnum'] = sys.argv[4]
    #articleID
    if not rec.has_key('p1'):
        for ul in artpage.body.find_all('ul', attrs = {'class' : 'title-volume-issue'}):
            for li in ul.find_all('li', attrs = {'class' : 'published'}):
                rec['p1'] = re.sub('.*, ', '', re.sub('\n', ' ', li.text.strip()))
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstract'}):
        for tit in div.find_all('title'):
            tit.replace_with('')
        rec['abs'] = div.text.strip()
        rec['abs'] = re.sub('[\n\t\r]', ' ', rec['abs'])
        rec['abs'] = re.sub('  +', ' ', rec['abs'])
    #references (only with DOI)
    for div in artpage.body.find_all('div', attrs = {'id' : 'references'}):
        for child in div.children:
            try:
                child.name
            except:
                continue
            if child.name == 'div':
                reference = child.text.strip()
            elif child.name == 'ul':
                for a in child.find_all('a'):
                    if a.text == 'CrossRef':
                        refdoi = re.sub('.*doi.org.', '', a['href'])
                        reference += ', DOI: ' + refdoi
            elif child.name == 'hr':
                rec['refs'].append([('x', reference)])
        #(new/other) references
        if not rec['refs']:
            for div2 in div.find_all('div', attrs = {'class' : 'ref'}):
                rec['refs'].append([('x', div2.text.strip())])
    #licence
    for div in artpage.body.find_all('div', attrs = {'class' : 'description'}):
        for div2 in div.find_all('div', attrs = {'class' : 'margin-top'}):
            div2text = div2.text.strip()
            if re.search('creativecommons.org', div2text):
                rec['licence'] = {'url' : re.sub('.*(http.*?creativecommons.*?0).*', r'\1', div2text)}
                for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                    rec['FFT'] = meta['content']
    #print rec
        



xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
