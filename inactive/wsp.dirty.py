#alte WSP auf unsererm FTP server von Hand laufen lassen
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
#import cookielib
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
wspdir = '/afs/desy.de/group/library/publisherdata/wsp'
def tfstrip(x): return x.strip()
publisher = 'WSP'


def concert(rawrecs):
    recs = []
    for rawrec in rawrecs:
        xmlrec = codecs.EncodedFile(codecs.open(rawrec,mode='rb'),'utf8')
        wsprecord = BeautifulSoup(''.join(xmlrec.readlines()))
        xmlrec.close()
        rec = {'tc' : 'P', 'note' : [], 'autaff' : [], 'keyw' : []}
        for jt in wsprecord.find_all('journal-title'):
            rec['jnl'] = jt.text
        for volume in wsprecord.find_all('volume'):
            rec['vol'] = volume.text
        for issue in wsprecord.find_all('issue'):
            rec['issue'] = issue.text
        for p1 in wsprecord.find_all('fpage'):
            rec['p1'] = p1.text
        for p2 in wsprecord.find_all('lpage'):
            rec['p2'] = p2.text
        for eid in wsprecord.find_all('elocation-id'):
            rec['p1'] = eid.text
        for title in wsprecord.find_all('article-title'):
            rec['tit'] = title.text
        for aid in wsprecord.find_all('article-id', attrs = {'pub-id-type' : 'doi'}):
            rec['doi'] = aid.text
        for sg in wsprecord.find_all('subj-group', attrs = {'subj-group-type' : 'heading'}):
            for s in sg.find_all('subject'):
                rec['note'].append(s.text)
        #affiliations
        affdict = {}
        for aff in wsprecord.find_all('aff'):
            affdict[aff.id] = aff.text
        for c in wsprecord.find_all('contrib', attrs = {'contrib-type' : 'author'}):
            for sn in c.find_all('string-name'):
                author = ''
                for surn in sn.find_all('surname'):
                    author += surn.text
                author += ', '
                for givenn in sn.find_all('given-names'):
                    author += givenn.text
            #no emails
            autaff = [author]
            for aff in c.find_all('aff'):
                autaff.append(aff.text)
            for xref in c.find_all('xref', attrs = {'ref-type' : 'aff'}):
                if affdict.has_key(xref.rid):
                    autaff.append(affdict[xref.rid])
            rec['autaff'].append(autaff)
        for date in wsprecord.find_all('date', attrs = {'date-type' : 'published'}):
            try:
                rec['date'] = '%s-%s-%s' % (date.year.text, date.month.text, date.day.text)
            except:
                try:
                    rec['date'] = '%s-%s' % (date.year.text, date.month.text)
                except:
                    try:
                        rec['date'] = date.year.text
                    except:
                        for sd in date.find_all('string-date'):
                            rec['date'] = re.sub('.* (\d\d\d\d) .*', r'\1', sd.text)
        if not rec.has_key('date'):
            for date in wsprecord.find_all('pub-date', attrs = {'pub-type' : 'ppub'}):
                try:
                    rec['date'] = '%s-%s-%s' % (date.year.text, date.month.text, date.day.text)
                except:
                    try:
                        rec['date'] = '%s-%s' % (date.year.text, date.month.text)
                    except:
                        rec['date'] = date.year.text
        for abstract in wsprecord.find_all('abstract'):
            rec['abs'] = ''
            for p in abstract.find_all('p'):
                rec['abs'] += p.text + ' '                
        for keywgrp in wsprecord.find_all('kwd-group'):
            for keyw in keywgrp.find_all('kwd'):
                rec['keyw'].append(keyw.text)
        for pagecount in wsprecord.find_all('page-count'):
            rec['pages'] = pagecount['count']
        #for  in wsprecord.find_all('', attrs = {'' : ''}):
        print rec
        recs.append(rec)
                                   
    return recs

for datei in os.listdir(wspdir):
    ordner = os.path.join(wspdir, datei)
    if not os.path.isdir(ordner): 
        continue
    elif datei in ['done', 'done2']:
        continue
    jnlfilename = 'WSP__'+datei
    print jnlfilename
    rawrecs = []
    for datei2 in os.listdir(ordner):
        ordner2 = os.path.join(ordner, datei2)
        for datei3 in os.listdir(ordner2):
            rawrecs.append(os.path.join(ordner2, datei3))
    print rawrecs
    recs = concert(rawrecs)
                        
    #sys.exit(0)

    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writeXML(recs,xmlfile,publisher)
    xmlfile.close()

    #retrival
    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
