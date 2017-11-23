#digest feeds from World Scientific Publishig
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
import zipfile

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
wspdir = '/afs/desy.de/group/library/publisherdata/wsp'
feeddir = '/afs/desy.de/group/library/preprints/incoming/WSP'
def tfstrip(x): return x.strip()
publisher = 'WSP'


#regular expressions for reference extraction
regexparx = re.compile('.*org\/abs\/')
regexpdoi = re.compile('.*genRefLink.*\'(10\.\d\d.*)\'.*')
regexpdoihtml = re.compile('%252F')
regexpdoihtml2 = re.compile('%253A') #:
regexpdoihtml3 = re.compile('%2528') #(
regexpdoihtml4 = re.compile('%2529') #)
regexpdoihtml5 = re.compile('%253C') #<
regexpdoihtml6 = re.compile('%253E') #>
regexpabs = re.compile('.*worldscientific.com\/doi\/(10.*?)\'.*')
regexpcr = re.compile('[\n\t\r]')



def getreferencesfromweb(doi):
    link = 'http://www.worldscientific.com/doi/ref/%s' % (doi)
    print '   ', link
    refpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(link))
    refs = []
    for li in refpage.body.find_all('li', attrs = {'class' : 'reference'}):
        for a in li.find_all('a'):
            if a.has_attr('href'):
                #arXiv-links
                if a.text in ['arXiv', 'arxiv', 'ARXIV']:
                    rn = regexparx.sub(',  arXiv: ', a['href']) + ', '
                    a.replace_with(rn)
                #WSP-DOI
                elif regexpabs.search(a['href']):
                    rdoi = regexpabs.sub(r', DOI: \1 , ', a['href'])
                    a.replace_with(rdoi)
        #Crossref-DOI
        for script in li.find_all('script'):
            scriptt = script.text
            if regexpdoi.search(scriptt):
                rdoi = regexpdoi.sub(r', DOI: \1 , ', scriptt)
                rdoi = regexpdoihtml.sub('/', rdoi)
                rdoi = regexpdoihtml2.sub(':', rdoi)
                rdoi = regexpdoihtml3.sub(')', rdoi)
                rdoi = regexpdoihtml4.sub('(', rdoi)
                rdoi = regexpdoihtml5.sub('<', rdoi)
                rdoi = regexpdoihtml6.sub('>', rdoi)
                script.replace_with(rdoi)
            else:
                script.replace_with(' ')
        #refextract
        reftext = regexpcr.sub(' ', li.text.strip())
        #print '     ', reftext
        refs.append([('x', reftext)])
    time.sleep(50)
    return refs


#mapping from WSP-xml to ejlmod2-format
def concert(rawrecs):
    recs = []
    print 'found %i xml files' % (len(rawrecs))
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
            for sup in aff.find_all('sup'):
                sup.replace_with('')
            affdict[aff['id']] = aff.text
        #print affdict
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
                if affdict.has_key(xref['rid']):
                    autaff.append(affdict[xref['rid']])
            rec['autaff'].append(autaff)
        #date
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
        #abstract
        for abstract in wsprecord.find_all('abstract'):
            rec['abs'] = ''
            for p in abstract.find_all('p'):
                rec['abs'] += p.text + ' '              
        #keywords
        for keywgrp in wsprecord.find_all('kwd-group'):
            for keyw in keywgrp.find_all('kwd'):
                rec['keyw'].append(keyw.text)
        #num of pages
        for pagecount in wsprecord.find_all('page-count'):
            rec['pages'] = pagecount['count']
        #references
        rec['refs'] = getreferencesfromweb(rec['doi'])
        recs.append(rec)                                   
    return recs





#check for new files
done = os.listdir(os.path.join(wspdir, 'done'))
filestodo = []
for zipdatei in os.listdir(feeddir):
    if not zipdatei in done and re.search('.zip$', zipdatei):
        filestodo.append(zipdatei)
print 'found %i new WSP zip-files to digest' % (len(filestodo))

#unzip new files
for zipdatei in filestodo:
    zfile = zipfile.ZipFile(os.path.join(feeddir, zipdatei))
    zfile.extractall(wspdir)

#checking extracted zip-files
for datei in os.listdir(wspdir):
    ordner = os.path.join(wspdir, datei)
    if not os.path.isdir(ordner): 
        continue
    elif datei in ['done']:
        continue
    #jnlfilename = 'WSP__'+datei
    jnlfilename = datei
    print jnlfilename
    rawrecs = []
    for datei2 in os.listdir(ordner):
        ordner2 = os.path.join(ordner, datei2)
        for datei3 in os.listdir(ordner2):
            rawrecs.append(os.path.join(ordner2, datei3))
    print rawrecs
    recs = concert(rawrecs)
    #save them
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

#move to 'done'
for zipdatei in filestodo:
    os.system('cp %s/%s %s/done/' % (feeddir, zipdatei, wspdir))

#clean WSP directory
for datei in os.listdir(wspdir):
    ordner = os.path.join(wspdir, datei)
    if not datei in ['done']:
        os.system('rm -rf %s' % (ordner))
    
