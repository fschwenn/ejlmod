# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Cambridge-journals
# FS 2015-02-12


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
import time
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Cambridge University Press'

jid =  sys.argv[1]
vol = sys.argv[2]
jnlfilename = 'cambridge'+jid + vol
if len(sys.argv) > 3:
    iss = sys.argv[3]
    jnlfilename += '.' + iss

if len(sys.argv) > 4:
    jnlfilename += '.' + sys.argv[4]

if jid == 'IAU':
    jnlname = 'IAU Symp.'
elif jid == 'PSP':
    jnlname = 'Math.Proc.Cambridge Phil.Soc.'
elif jid == 'FMS':
    jnlname = 'SIGMA'
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


toclink = 'http://journals.cambridge.org/action/displayIssue?jid=%s&volumeId=%s' % (jid, vol)
if len(sys.argv) > 3:
    toclink += '&issueId=%s' % (iss)
    print toclink
        
try:
    toc = BeautifulSoup(urllib2.urlopen(toclink, timeout=300))
except:
    print "retry in 180 seconds"
    time.sleep(180)
    toc = BeautifulSoup(urllib2.urlopen(toclink, timeout=300))

recs = []
for div in toc.body.find_all('div', attrs = {'class' : 'tableofcontents'}):
    for p in div.find_all('p'):
        note = re.sub('\xa0', ' ', re.sub('[\t\n\r]', ' ', p.text))
        note = re.sub('Table of Contents * \-', '', note)
        note = re.sub('Volume *\w* *\-', '', note)
        note = re.sub('Issue *\w* *\-', '', note)
        note = re.sub('  +', '', note).strip()

for a in toc.body.find_all('a', attrs = {'title' : 'Abstract'}):
    rec = {'jnl' : jnlname, 'keyw' : [], 'note' : [note]}
    if len(sys.argv) > 4:
        rec['cnum'] = sys.argv[4]
    if jid in ['IAU']: 
        rec['tc'] = 'C'
        rec['vol'] = iss[1:]
        if rec['vol'] == '308':
            rec['cnum'] = 'C14-06-23.11'
        elif rec['vol'] == '306':
            rec['cnum'] = 'C14-05-25.1'
        elif rec['vol'] == '313':
            rec['cnum'] = 'C14-09-15.13'
        elif rec['vol'] == '312':
            rec['cnum'] = 'C14-08-25.9'
    else:
        rec['tc'] = 'P'
        rec['vol'] = vol
        if len(sys.argv) > 3:
            rec['issue'] = iss
    artlink = 'http://journals.cambridge.org/action/' + a['href']
    try:
        #print 'artlink', artlink
        art = BeautifulSoup(urllib2.urlopen(artlink, timeout=300))
        time.sleep(2)
    except:
        print "retry in 180 seconds"
        time.sleep(180)
        art = BeautifulSoup(urllib2.urlopen(artlink, timeout=300))
    #OA
    for ul in art.body.find_all('ul', attrs = {'class' : 'jnlDetails'}):
        for li in ul.find_all('li'):
            if re.search('creativecommons', li.text):
                rec['licence'] = {'url' : re.sub('.*(http:\/\/creativecommons.org.*?0).*', r'\1', li.text).strip()}
    #Title, Abstract
    for meta in art.head.find_all('meta'):
        if meta.has_attr('property'):
            if meta['property'] == 'og:title':
                rec['tit'] = meta['content']
            if meta['property'] == 'og:description':
                rec['abs'] = meta['content']
    #Date, Pages, Keywords
    for meta in art.body.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
            if meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            if meta['name'] == 'citation_lastpage':
                if meta['content'] != '':
                    rec['p2'] = meta['content']
                else:
                    for ul in art.body.find_all('ul', attrs = {'class' : 'jnlDetails'}):
                        for li in ul.find_all('li'):
                            litext = li.text
                            if re.search('Volume.*page', litext):
                                rec['p1'] = re.sub('.*, (\d+) \(\d+ page.*', r'\1', litext)
                                rec['pages'] = re.sub('.*, \d+ \((\d+) page.*', r'\1', litext)                    
                                break
            if meta['name'] == 'citation_keywords':
                if re.search(ur'\u2014', meta['content']):
                    for kw in re.split(ur'\u2014', meta['content']): 
                       rec['keyw'].append(kw.strip())
                else:
                    for kw in re.split(';',  meta['content']):
                        rec['keyw'].append(kw.strip())
    #DOI
    for a in art.body.find_all('a', attrs = {'class' : 'cboDOI'}):
        rec['doi'] = re.sub('.*dx.doi.org.', '', a.string).strip()
        print rec['doi']
    #Authors
    descriptionboxs  = art.body.find_all('div', attrs = {'class' : 'description-box'})
    if len(descriptionboxs) == 0:
        print 'NO AUTHORS???'
        rec['auts'] = ['John Doe']
    elif len(descriptionboxs[0].find_all('h3', attrs = {'class' : 'author'})) == 0:
        print 'NO AUTHORS??'
        rec['auts'] = ['John Doe']        
    else:
        for h3 in descriptionboxs[0].find_all('h3', attrs = {'class' : 'author'}):
            for sup in h3.find_all('sup'):
                try:
                    if re.search('[a-z0-9]', sup.a.string):
                        cont = re.sub('^[a-z]*', '', sup.a.string)
                        sup.replace_with(', =Aff%s' % (cont))
                    else:
                        sup.replace_with('')
                except:
                    try:
                        cont = re.sub('^[a-z]*', '', sup.string)
                        if re.search('[a-z0-9]', cont):
                            sup.replace_with(', =Aff%s' % (cont))
                        else:
                            sup.replace_with('')
                    except:
                        print 'author problem??', h3
        rec['auts'] = re.split(', ', re.sub(' and ', ', ', re.sub('\xa0', ' ', h3.text)))
        #Affiliations
        for p in descriptionboxs[0].find_all('p'):
            for sup in p.find_all('sup'):
                try:
                    cont = re.sub('^[a-z]*', '', sup.string.strip())
                    sup.replace_with('XXX Aff%s= ' % (cont))
                except:
                    pass
            if p.has_attr('class') and 'smallcopy' in p['class']:
                p.replace_with('DIRTYSTART')
            elif p.has_attr('class') and 'section-title' in  p['class']:
                p.replace_with('DIRTYSTOP')
        affstring = re.sub(' *\n *', ' ', descriptionboxs[0].text)
        affstring = re.sub('.*DIRTYSTART(.*)DIRTYSTOP.*', r'\1', affstring).strip()
        affstring = re.sub('  +' , ' ', affstring)
        rec['aff'] = re.split(' *XXX *', affstring)
    #References
    for a in art.body.find_all('a', attrs = {'class' : 'article-ref'}):
    #if 1==0:
        reflink = 'http://journals.cambridge.org/action/' + a['href']
        reflink = re.sub('[\r\t\n ]', '', reflink)
        try:
            #print 'reflink', reflink
            ref = BeautifulSoup(urllib2.urlopen(reflink))
        except:
            print "retry in 180 seconds"
            time.sleep(180)
            ref = BeautifulSoup(urllib2.urlopen(reflink))
        rec['refs'] = []
        fulltxt = ref.body.find_all('div', attrs = {'class' : 'fulltxt'})
        if fulltxt:
            for li in fulltxt[0].find_all('li'):
                if li.has_attr('id'):
                    ref = [('o',  re.sub('ref', '', li['id']))]
                    for a in li.find_all('a'):
                        if a.has_attr('href') and re.search('dx.doi.org', a['href']):
                            ref.append(('a', re.sub('.*dx.doi.org.', '', a['href'])))
                    if len(ref) == 1:      
                        ref = [('x', li.text)]
                    rec['refs'].append(ref)
        else:
            print 'no references (?)'
    recs.append(rec)






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
