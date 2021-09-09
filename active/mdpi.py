# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest MDPI journals (Universe, Symmetry, Sensors, Instruments, Galaxies, Entropy, Atoms)
# FS 2017-07-17

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special/'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

def tfstrip(x): return x.strip()

publisher = 'MDPI'
jnl = sys.argv[1]
if jnl in ['proceedings', 'psf']:
    vol = sys.argv[2]
    iss = sys.argv[3]
    cnum = sys.argv[4]

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

#journals have quite different number of articles per month
if jnl == 'symmetry': #2211
    numberofpages = 27
elif jnl == 'universe': #367
    numberofpages = 7
elif jnl == 'sensors': #9570
    numberofpages = 60
elif jnl == 'instruments': #91
    numberofpages = 3
elif jnl == 'galaxies': #231
    numberofpages = 4
elif jnl == 'entropy': #2124
    numberofpages = 16
elif jnl == 'particles': #53
    numberofpages = 4
elif jnl == 'physics': #26
    numberofpages = 4
elif jnl == 'condensedmatter': #139
    numberofpages = 3
elif jnl == 'atoms': #173
    numberofpages = 3
elif jnl == 'mathematics':
    numberofpages = 35
elif jnl == 'quantumrep':
    numberofpages = 4
elif jnl == 'axioms':
    numberofpages = 6
elif jnl == 'applsci':
    numberofpages = 100
elif jnl == 'information':
    numberofpages = 7



conferences = {'Selected Papers from the 1st International Electronic Conference on Universe (ECU 2021)' : 'C21-02-22',
               'Selected Papers from the 17th Russian Gravitational Conference —International Conference on Gravitation, Cosmology and Astrophysics (RUSGRAV-17)' : 'C20-06-28'}

chunksize = 50

rpp = 10
startyear = now.year-1
if jnl == 'proceedings':
    #starturl = 'http://www.mdpi.com/2504-3900/%s/%s' % (vol, iss)
    #starturl = 'https://www.mdpi.com/journal/universe/special_issues/quantum_fields'
    jnlfilename = 'mdpi_proc%s.%s_%s' % (vol, iss, cnum)
    done = []
elif jnl == 'psf':
    starturl = 'http://www.mdpi.com/2673-9984/%s/%s' % (vol, iss)
    jnlfilename = 'mdpi_psf%s.%s_%s' % (vol, iss, cnum)
    done = []
else:
    starturl = 'http://www.mdpi.com/search?journal=%s&year_from=%i&year_to=2150&page_count=%i&sort=pubdate&view=default' % (jnl, startyear, rpp)
    jnlfilename = '%s.%s_%i' % (jnl, stampoftoday, rpp*numberofpages)
    done =  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))
    done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/%4d/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, now.year-1, jnl)))
    done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/onhold/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))


    done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/zu_punkten/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))
    done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/zu_punkten/enriched/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))
    
    print 'already done:', len(done)


refmissing = ['10.3390/e22040380', '10.3390/e22040389', '10.3390/e22040390', '10.3390/e22040391', '10.3390/e22040394', '10.3390/e22040395', '10.3390/e22040396', '10.3390/e22040398', '10.3390/e22040399', '10.3390/e22040400', '10.3390/e22040401', '10.3390/e22040402', '10.3390/e22040403', '10.3390/e22040404', '10.3390/e22040405', '10.3390/e22040407', '10.3390/e22040409', '10.3390/e22040411', '10.3390/particles3010019', '10.3390/particles3020020', '10.3390/particles3020021', '10.3390/particles3020022', '10.3390/particles3020023', '10.3390/particles3020024', '10.3390/particles3020025', '10.3390/particles3020026', '10.3390/physics2020008', '10.3390/sym12040515', '10.3390/sym12040517', '10.3390/sym12040522', '10.3390/sym12040534', '10.3390/sym12040537', '10.3390/sym12040542', '10.3390/sym12040543', '10.3390/sym12040554', '10.3390/sym12040558', '10.3390/sym12040568', '10.3390/sym12040569', '10.3390/sym12040570', '10.3390/sym12040572', '10.3390/sym12040573', '10.3390/sym12040579', '10.3390/sym12040585', '10.3390/sym12040593', '10.3390/sym12040595']


hdr = {'User-Agent' : 'Mozilla/5.0'}
artlinks = []
if jnl == 'proceedings':
    #starturl = 'https://www.mdpi.com/journal/symmetry/special_issues/mttd2019_symmetry'
    starturl = 'https://www.mdpi.com/journal/information/special_issues/machine_learning_accelerator_technology'
    #done = []  
    print starturl
    req = urllib2.Request(starturl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'article-content'})
    for div in divs:
        for a in div.find_all('a', attrs = {'class' : 'title-link'}):
            artlinks.append(('http://www.mdpi.com' + a['href'], a.text))
else:
    for j in range(numberofpages):
        print '==={ %i/%i }==={ %s&page_no=%i }===' % (j+1, numberofpages, starturl, j+1)
        req = urllib2.Request('%s&page_no=%i' % (starturl, j+1), headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        divs = tocpage.body.find_all('div', attrs = {'class' : 'article-content'})
        for div in divs:
            for a in div.find_all('a', attrs = {'class' : 'title-link'}):
                if not ('http://www.mdpi.com' + a['href'], a.text) in artlinks:
                    artlinks.append(('http://www.mdpi.com' + a['href'], a.text))
        print '  %i article links so far ' % (len(artlinks))
        time.sleep(3)

#done = []


numberofchunks = (len(artlinks)-1) / chunksize + 1 

i=0
recs = []
for artlink in artlinks:
    rec = {'jnl' : jnl.title(), 'tc' : 'P', 'keyw' : [], 'aff' : [], 'auts' : [],
           'note' : [], 'refs' : []}
    #rec['tc'] = 'C'
    #rec['cnum'] = 'C19-09-01'
    #rec['jnl'] = 'Symmetry'
    i += 1
    #title and link
    if jnl == 'proceedings':
        rec['jnl'] = 'MDPI Proc.'
        rec['tc'] = 'C'
        rec['cnum'] = cnum
    elif jnl == 'psf':
        rec['jnl'] = 'Phys.Sci.Forum'
        rec['tc'] = 'C'
        rec['cnum'] = cnum
    elif jnl == 'condensedmatter':
        rec['jnl'] = 'Condens.Mat.'
    elif jnl == 'physics':
        rec['jnl'] = 'MDPI Physics'
    elif jnl == 'quantumrep':
        rec['jnl'] = 'Quantum Rep.'
    elif jnl == 'applsci':
        rec['jnl'] = 'Appl.Sciences'
    print '---{ %3i/%3i (%i) }---{ %s }---' % (i, len(artlinks), len(recs), artlink[0])
    rec['FFT'] = artlink[0] + '/pdf'
    rec['tit'] = artlink[1]
    #get detailed page
    try:
        time.sleep(1)
        artreq = urllib2.Request(artlink[0], headers=hdr)
        page = BeautifulSoup(urllib2.urlopen(artreq))
    except:
        print '   ... wait 15 minutes'
        time.sleep(900)
        artreq = urllib2.Request(artlink[0], headers=hdr)
        page = BeautifulSoup(urllib2.urlopen(artreq))
    ##Review?1
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.type'}):
        if meta['content'] == 'Review': rec['tc'] = 'R'
    for atype in page.find_all('span', attrs = {'class' : 'label articletype'}):
        rec['note'].append(atype.text)
        if atype.text == 'Review':
            rec['tc'] = 'R'
    ##Date
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.date'}):
        rec['date'] = meta['content']
    ##licence
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.rights'}):
        rec['licence'] = {'url' : re.sub('\/$', '', meta['content'])}
    ##keywords
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.subject'}):
        if meta['content'] != 'n/a':
            rec['keyw'].append(meta['content'])
    ##pbn
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.volume'}):
        rec['vol'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.number'}):
        rec['issue'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.startingPage'}):
        rec['p1'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.endingPage'}):
        rec['p2'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_doi'}):
        rec['doi'] = meta['content']
    if rec['doi'] in done and not rec['doi'] in refmissing:
        print '  %s already in done'  % (rec['doi'])
    else:
        ##abstract
        for meta in page.head.find_all('meta', attrs = {'name' : 'dc.description'}):
            rec['abs'] = meta['content']
        ##special issue
        for div in page.body.find_all('div', attrs = {'class' : 'belongsTo'}):
            if re.search('Special Issue', div.text):
                for a2 in div.find_all('a'):
                    rec['note'].append([ a2.text ])
                    if a2.text in conferences.keys():
                        rec['tc'] = 'C'
                        rec['cnum'] = conferences[a2.text]
        ##authors and affiliations
        for div in page.body.find_all('div', attrs = {'class' : 'art-authors'}):
    #        for div in diva.find_all('div', attrs = {'class' : 'author'}):
                for sup in div.find_all('sup'):
                    newcont = ''
                    for cont in re.split(' *, *', sup.text):
                        if re.search('\d', cont):
                            newcont += ' , =Aff%s, ' % (cont.strip())
                    sup.replace_with(newcont)
                for script in page.body.find_all('script'):
                    script.replace_with('')
                #ORCIDs
                for a in div.find_all('a', attrs = {'itemprop' : 'author'}):
                    if a.has_attr('href') and re.search('orcid=[0-9]', a['href']):
                        orcid = re.sub('.*orcid=', 'ORCID:', a['href'])
                        author = a.text.strip()
                        a.replace_with('%s; %s' % (author, orcid))
                authors = re.sub(' and ', ' , ', re.sub('\xa0', ' ', div.text))
                authors = re.sub('[\n\t]', '', authors)
                authors = re.sub('&nbsp;', ' ', authors)
                authors = re.sub('^ *by *', '', authors)
                authors = re.sub('\*', ' ', authors)
                for author in re.split(' *, *', authors):
                    if len(author.strip()) > 2:
                        if re.search('ORCID', author):
                            parts = re.split(' *; *', author)
                            rec['auts'].append('%s, %s' % (ejlmod2.shapeaut(parts[0]), parts[1]))
                        else:
                            rec['auts'].append(author.strip())
        for diva in page.body.find_all('div', attrs = {'class' : 'art-affiliations'}):
            for div in diva.find_all('div', attrs = {'class' : 'affiliation'}):
                for sup in div.find_all('sup'):
                    sup.replace_with('Aff%s= ' % (sup.text))
                for span in div.find_all('span'):
                    span.replace_with(';;;')
                for aff in re.split(' *;;; *', re.sub('[\n\t]', '', div.text)):
                    rec['aff'].append(aff.strip())
        #references
        reflink = artlink[0]  + '/htm'
        print '              ---{ %s }---' % (reflink)
        try:
            refreq = urllib2.Request(reflink, headers=hdr)
            refpage = BeautifulSoup(urllib2.urlopen(refreq))
        except:
            print '   could not get references'
        for section in refpage.body.find_all('section', attrs = {'id' : 'html-references_list'}):
            for li in section.find_all('li'):
                for a2 in li.find_all('a', attrs = {'class' : 'cross-ref'}):
                    rdoi = re.sub('.*doi\.org\/', 'doi: ', a2['href'])
                    a2.replace_with(rdoi)
                for a2 in li.find_all('a'):
                    a2.replace_with('')
                lit = re.sub('\[\]', '', li.text.strip())
                lit = re.sub('\.? *\[(doi:.*?)\]', r', \1', lit)
                lit = re.sub('\.? *\[(http.*?)\]', r', \1', lit)
                lit = re.sub('\[Google Scholar\]', '', lit)
                #Semikolon between authors
                lit = re.sub('([A-Z]\.); ([A-Z][a-zA-Z\-]+), ([A-Z\.]+);', r'\1, \2 \3,', lit)
                lit = re.sub('([A-Z]\.); ([A-Z][a-zA-Z\-]+), ([A-Z\.]+);', r'\1, \2 \3,', lit)
                rec['refs'].append([('x', lit)])
        #early access
        for strong in page.body.find_all('strong'):
            if re.search('is an early access version', strong.text):
                print 'skip early acccess version'
        else:
            recs.append(rec)
            print '  ', rec.keys()
        time.sleep(3)
    if (i % chunksize == 0) or (i == len(artlinks)):
        #write xml
        if recs:
            if i % chunksize == 0:
                xmlfilename = '%s-%02i_of_%i.xml' % (jnlfilename, i/chunksize, numberofchunks)
            else:
                xmlfilename = '%s-fin_of_%i.xml' % (jnlfilename, numberofchunks)
            xmlf = os.path.join(xmldir, xmlfilename)
            xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
            ejlmod2.writenewXML(recs, xmlfile, publisher, xmlfilename[:-4])
            xmlfile.close()
            #retrival
            retfiles_text = open(retfiles_path, "r").read()
            line = '%s\n' % (xmlfilename)
            print ' + wrote %s' % (line)
            if not line in retfiles_text:
                retfiles = open(retfiles_path,"a")
                retfiles.write(line)
                retfiles.close()
        recs = []
            
