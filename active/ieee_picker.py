# -*- coding: utf-8 -*-
#program to harvest individual IEEE articles bei DOIs
#FS: 2018-01-26

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import time
import datetime
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'IEEE'

jnlfilename = 'ieee_picker-%s' % (stampoftoday)
urltrunc = "http://ieeexplore.ieee.org"

dois = sys.argv[1:]

def meta_with_name(tag):
    return tag.name == 'meta' and tag.has_attr('name')
    
def fsunwrap(tag):
    try: 
        for i in tag.find_all('i'):
            cont = i.string
            i.replace_with(cont)
    except:
        print 'fsunwrap-i-problem'
    try: 
        for b in tag.find_all('b'):
            cont = b.string
            b.replace_with(cont)
    except:
        print 'fsunwrap-b-problem'
    try: 
        for sup in tag.find_all('sup'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('sub'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    try: 
        for form in tag.find_all('formula',attrs={'formulatype': 'inline'}):
            form.replace_with(' [FORMULA] ')
    except:
        print 'fsunwrap-form-problem'
    return tag

def referencetostring(reference):
    refstring = re.sub('\s+',' ',fsunwrap(reference).prettify())
    refstring = re.sub('<li> *(.*) *<br.*',r'\1',refstring)
    for a in reference.find_all('a'):
        if a.has_attr('href') and re.search('dx.doi.org\/',a['href']):
            refstring += ', doi: %s' % (re.sub('.*dx.doi.org\/','',a['href']))
    return refstring




recs = []
i = 0
for doi in dois:
    i += 1
    print '---{ %i/%i }---{ %s}------' % (i, len(dois), doi)
    tc = 'P'
    rec = {'keyw' : [], 'autaff' : [], 'tc' : tc}
    try:
        articlepage = BeautifulSoup(urllib2.urlopen('http://dx.doi.org/%s' % (doi),timeout=300))
        time.sleep(6)
    except:
        print "retry in 60 seconds"
        time.sleep(60)
        articlepage = BeautifulSoup(urllib2.urlopen('http://dx.doi.org/%s' % (doi),timeout=300))
    #metadata now in javascript
    for script in articlepage.find_all('script', attrs = {'type' : 'text/javascript'}):
        if re.search('global.document.metadata', script.text):
            gdm = re.sub('[\n\t]', '', script.text).strip()
            gdm = re.sub('.*global.document.metadata=(\{.*\}).*', r'\1', gdm)
            gdm = json.loads(gdm)
    rec['jnl'] = gdm['publicationTitle']
    if rec['jnl'] == 'IEEE Computer Graphics and Applications':
        rec['jnl'] = 'IEEE Comp.Graph.App.'
    elif rec['jnl'] == 'IEEE Sensors Journal':
        rec['jnl'] = 'IEEE Sensors J.'
    elif rec['jnl'] == 'IEEE Transactions on Applied Superconductivity':
        rec['jnl'] = 'IEEE Trans.Appl.Supercond.'
    elif rec['jnl'] == 'IEEE Transactions on Circuits and Systems I: Regular Papers':
        rec['jnl'] = 'IEEE Trans.Circuits Theor.'
    elif rec['jnl'] == 'IEEE Transactions on Magnetics':
        rec['jnl'] = 'IEEE Trans.Magnetics'
    elif rec['jnl'] == 'IEEE Transactions on Nuclear Science':
        rec['jnl'] = 'IEEE Trans.Nucl.Sci.'
    elif rec['jnl'] == 'Journal of Lightwave Technology':
        rec['jnl'] = 'J.Lightwave Tech.'
    else:
        rec['jnl'] = 'BOOK'

    if gdm.has_key('authors'):
        for author in gdm['authors']:
            autaff = [author['name']]
            if author.has_key('affiliation'):
                autaff.append(author['affiliation'])
            if author.has_key('orcid'):
                autaff.append('ORCID:'+author['orcid'])
            rec['autaff'].append(autaff)
    if rec['jnl'] in ['IEEE Trans.Magnetics', 'IEEE Trans.Appl.Supercond.']:
        if gdm.has_key('externalId'):
            rec['p1'] = gdm['externalId']
        elif gdm.has_key('articleNumber'):
            rec['p1'] = gdm['articleNumber']
        else:
            rec['p1'] = gdm['startPage']
            rec['p2'] = gdm['endPage']
    else:
        if gdm.has_key('endPage'):
            rec['p1'] = gdm['startPage']
            rec['p2'] = gdm['endPage']
        elif gdm.has_key('externalId'):
            rec['p1'] = gdm['externalId']
        else:
            rec['p1'] = gdm['articleNumber']
    if gdm['isFreeDocument']:
        rec['FFT'] = urltrunc + gdm['pdfPath']
    rec['tit'] = gdm['formulaStrippedArticleTitle']
    if gdm.has_key('abstract'):
        rec['abs'] = gdm['abstract']
    ## mistake in metadata
    if re.search('\d+ pp', gdm['startPage']):
        rec['pages'] = re.sub(' .*', '', gdm['startPage'])
        rec['p1'] = str(int(gdm['endPage']) - int(rec['pages']) + 1)            
    else:
        try:
            rec['pages'] = int(re.sub(' .*', '', gdm['endPage'])) - int(gdm['startPage']) + 1
        except:
            pass
    rec['doi'] = gdm['doi']
    if gdm.has_key('keywords'):
        for kws in gdm['keywords']:
            for kw in kws['kwd']:
                if not kw in rec['keyw']:
                    rec['keyw'].append(kw)
    try:
        rec['date'] = re.sub('\.', '', gdm['journalDisplayDateOfPublication'])
    except:
        rec['date'] = re.sub('\.', '', gdm['publicationDate'])
    rec['year'] = rec['date'][-4:]
    if gdm.has_key('issue'):
        rec['issue'] = gdm['issue']
    if gdm.has_key('volume'):
        rec['vol'] = gdm['volume']
    if gdm['isConference']:
        rec['tc'] = 'C'
        rec['note'] = [gdm['publicationTitle']]

    recs.append(rec)
    




#closing of files and printing
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
