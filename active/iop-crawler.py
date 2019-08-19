# -*- coding: UTF-8 -*-
# crawls iop web page to get metadata of journal issue
# FS 2017-05-15

import os
import sys
#import xml.dom.minidom
#import xml.sax
#myParser = xml.sax.make_parser()
#import urllib
import ejlmod2
import re
import time
import codecs
from bs4 import BeautifulSoup
import urllib2
import urlparse

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
publisher = 'IOP'
regexpiopurl = re.compile('http...iopscience.iop.org.')
regexpdxdoi = re.compile('http...dx.doi.org.')
#collapseWs = re.compile('[\n \t]+')
#initialEnd = re.compile(r'([A-Z])\b')

starturls = re.split(',', sys.argv[1])
issns = [re.sub('.*\/(\d\d\d\d\-\d\d\d.)\/.*', r'\1', starturl) for starturl in starturls]
if len(set(issns)) > 1:
    print 'several issues only works (at the moment) not for different journals'
    print set(issns)
    sys.exit(0)
else:
    issn = issns[0]

jnls = {'1538-3881': 'Astron.J.',
        '0004-637X': 'Astrophys.J.',
        '1538-4357': 'Astrophys.J.',
        '2041-8205': 'Astrophys.J.',
        '0067-0049': 'Astrophys.J.Supp.',
        '0264-9381': 'Class.Quant.Grav.',
        '1009-9271': 'Chin.J.Astron.Astrophys.',
        '1009-1963': 'Chin.Phys.',
        '1674-1056': 'Chin.Phys.',
        '1674-1137': 'Chin.Phys.',
        '0256-307X': 'Chin.Phys.Lett.',
        '0253-6102': 'Commun.Theor.Phys.',
        '0143-0807': 'Eur.J.Phys.',
        '0295-5075': 'EPL',
        '1757-899X': 'IOP Conf.Ser.Mater.Sci.Eng.',
        '1751-8121': 'J.Phys.',
        '1742-6596': 'J.Phys.Conf.Ser.',
        '0954-3899': 'J.Phys.',
        '1361-6463': 'J.Phys.',
        '1475-7516': 'JCAP ',
        '1126-6708': 'JHEP ',
        '1748-0221': 'JINST ',
        '1742-5468': 'JSTAT ',
        '0957-0233': 'Measur.Sci.Tech.',
        '1367-2630': 'New J.Phys.',
        '0031-9120': 'Phys.Educ.',
        '1063-7869': 'Phys.Usp.',
        '0034-4885': 'Rep.Prog.Phys.',
        '1674-4527': 'Res.Astron.Astrophys.',
        '1402-4896': 'Phys.Scripta',        
        '0953-2048': 'Supercond.Sci.Technol.',
        '2399-6528': 'J.Phys.Comm.',
        '1757-899X': 'IOP Conf.Ser.Mater.Sci.Eng.',
        '0036-0279': 'Russ.Math.Surveys',
        '0951-7715': 'Nonlinearity',
        '0953-4075': 'J.Phys.',
        '0953-8984': 'J.Phys.Condens.Matter',
        '0031-9155': 'Phys.Med.Biol.',
        '1538-3873': 'Publ.Astron.Soc.Pac.',
        '2399-6528': 'J.Phys.Comm.',
        '0741-3335': 'Plasma Phys.Control.Fusion',
        '0026-1394': 'Metrologia'}
jnls['2516-1067'] = 'Plasma Res.Express'
if jnls.has_key(issn):
    jnl = jnls[issn]
else:
    print 'journal not known'
    sys.exit(0)
tocpages = []
j = 0
for starturl in starturls:
    j += 1
    try:
        print '---{ %i/%i }---{ %s }---' % (j, len(starturls), starturl)
        tocpages.append(BeautifulSoup(urllib2.urlopen(starturl, timeout=300)))
        time.sleep(10)
    except:
        print 'try "%s" again after 5 minutes' % (starturl)
        time.sleep(300)
        tocpages.append(BeautifulSoup(urllib2.urlopen(starturl, timeout=300)))
    
recs = []
voliss = []
vols = []
j = 0
for tocpage in tocpages:
    j += 1
    print '---------{_} %i/%i {_}---------' % (j, len(tocpages))
    issnote = False
    h3note = False
    h4note = False
    for div in tocpage.find_all('div', attrs = {'id' : 'wd-jnl-issue-title'}):
        for h4 in div.find_all('h4'):
            issnote = h4.text
    for div in tocpage.find_all('div', attrs = {'id' : 'wd-jnl-issue-art-list'}):
        for child in div.children:
            try:
                child.name
            except:
                continue
            if child.name == 'h3':
                h4note = False
                h3note = child.text
                print '===%s===' % (h3note)
            elif child.name == 'h4':
                h4note = child.text
                print '---%s---' % (h4note)
            elif child.name == 'div':
                for a in child.find_all('a', attrs = {'class' : 'art-list-item-title'}):
                    time.sleep(30)
                    rec = {'jnl' : jnl, 'note' : [], 'tc' : 'P', 'autaff' : [], 'refs' : []}
                    orcidsfound = False
                    if len(sys.argv) > 2:
                        rec['cnum'] = sys.argv[2]
                        rec['tc'] = 'C'
                    elif issn in ['1742-6596', '1757-899X']:
                        rec['tc'] = 'C'
                    if issnote: rec['note'].append(issnote)
                    if h3note: rec['note'].append(h3note)
                    if h4note: rec['note'].append(h4note)
                    artlink = 'http://iopscience.iop.org' + a['href']
                    if artlink in ['http://iopscience.iop.org/article/10.1088/0953-4075/48/23/239501']:
                        rec = recs[-1]
                        continue
                    try:
                        artpage = BeautifulSoup(urllib2.urlopen(artlink, timeout=300))
                    except:
                        print 'try "%s" again after 5 minutes' % (artlink)
                        time.sleep(300)
                        artpage = BeautifulSoup(urllib2.urlopen(artlink, timeout=300))
                    autaff = False
                    #licence
                    for divl in artpage.body.find_all('div', attrs = {'class' : 'col-no-break wd-jnl-art-license media'}):
                        for a in divl.find_all('a'):
                            if a.has_attr('href'):
                                if re.search('creativecommons.org', a['href']):
                                    rec['licence'] = {'url' : a['href']}       
                    #metadata
                    for meta in artpage.find_all('meta'):
                        if meta.has_attr('name'):
                            if meta['name'] == 'citation_title':
                                rec['tit'] = meta['content']
                            elif meta['name'] == 'citation_online_date':
                                rec['date'] = meta['content']
                            elif meta['name'] == 'citation_volume':
                                if issn in ['1674-1056', '0953-4075']:
                                    rec['vol'] = 'B' + meta['content']
                                elif issn == '1674-1137':
                                    rec['vol'] = 'C' + meta['content']
                                elif issn == '1751-8121':
                                    rec['vol'] = 'A' + meta['content']
                                elif issn == '0954-3899':
                                    rec['vol'] = 'G' + meta['content']
                                elif issn == '1361-6463':
                                    rec['vol'] = 'D' + meta['content']
                                else:
                                    rec['vol'] = meta['content']
                            elif meta['name'] == 'citation_issue':
                                rec['issue'] = meta['content']
                            elif meta['name'] == 'citation_firstpage':
                                rec['p1'] = meta['content']
                            elif meta['name'] == 'citation_doi':
                                rec['doi'] = meta['content']
                            elif meta['name'] == 'citation_pdf_url' and rec.has_key('licence'):
                                rec['FFT'] = meta['content']
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
                                email = meta['content']
                                autaff.append('EMAIL:%s' % (email))
                    #JCAP
                    if issn == '1475-7516':
                        rec['vol'] = '%s%02i' % (rec['date'][2:4], int(rec['issue']))
                        del rec['issue']
                    if autaff:
                        rec['autaff'].append(autaff)
                    #authors if no ORCIDs in meta-section
                    if not orcidsfound or not rec['autaff']:
                        (auts, aff) = ([], [])
                        for authorsection in artpage.body.find_all('span'):
                            if authorsection.has_attr('data-authors'):
                                break
                        for span in authorsection.find_all('span', attrs = {'itemprop' : 'author'}):
                            orcid = False
                            affis = []
                            for sup in span.find_all('sup'):
                                affis = re.split(' *, *', sup.text)
                                sup.replace_with('')
                            author = re.sub('(.*) (.*)', r'\2, \1', span.text.strip())
                            for a in span.find_all('a'):
                                if a.has_attr('href') and re.search('orcid.org', a['href']):
                                    orcid = re.sub('.*orcid.org\/(\d.*[\dX])', r'\1', a['href'])
                            if orcid:
                                auts.append('%s, ORCID:%s' % (author, orcid))
                                orcidsfound = True
                            else:
                                auts.append(author)
                            for affi in affis:
                                auts.append('=Aff%s' % (affi))
                        for diva in artpage.body.find_all('div', attrs = {'class' : 'wd-jnl-art-author-affiliations'}):
                            for p in diva.find_all('p'):
                                for sup in p.find_all('sup'):
                                    affi = sup.text
                                    sup.replace_with('Aff%s= ' % (affi))
                                aff.append(p.text)
                        if len(auts) >= len(rec['autaff']):
                            del rec['autaff']
                            rec['auts'] = auts
                            rec['aff'] = aff
                    #abstract
                    for abstr in artpage.body.find_all('div', attrs = {'class' : 'article-text wd-jnl-art-abstract cf'}):
                        rec['abs'] = abstr.text.strip()
                    #keywords:
                    for divk in artpage.body.find_all('div', attrs = {'class' : 'wd-jnl-aas-keywords'}):
                        rec['keyw'] = []
                        for a in divk.find_all('a'):
                            rec['keyw'].append(a.text)
                    #get rid of footnotes
                    for ul in artpage.body.find_all('ul', attrs = {'class' : 'clear-list wd-content-footnotes'}):
                        ul.replace_with('')      
                    #references
                    for li in artpage.body.find_all('li', attrs = {'class' : 'indices-list'}):
                        for a in li.find_all('a',  attrs = {'class' : 'indices-id'}):
                            nummer = a.text
                            a.replace_with(nummer + ' ')
                        for a in li.find_all('a',  attrs = {'title' : 'CrossRef'}):
                            if a.has_attr('href'):
                                doi = regexpdxdoi.sub(', DOI: ', a['href'])
                                a.replace_with(doi)
                        for a in li.find_all('a',  attrs = {'title' : 'IOPScience'}):
                            if a.has_attr('href'):
                                doi = regexpiopurl.sub(', DOI: 10.1088/', a['href'])
                                a.replace_with(doi)
                        for a in li.find_all('a',  attrs = {'title' : 'IOPscience'}):
                            if a.has_attr('href'):
                                doi = regexpiopurl.sub(', DOI: 10.1088/', a['href'])
                                a.replace_with(doi)
                        for a in li.find_all('a'):
                            if re.search('Google.?Scholar', a.text) or re.search('ADS', a.text):
                                a.replace_with('')
                            elif a.has_attr('href'):
                                link = ', %s: %s' % (a.text, a['href'])
                                a.replace_with(link)
                        ref = li.text
                        if regexpdxdoi.search(ref):
                            ref = regexpdxdoi.sub('DOI: ', ref)
                        if regexpiopurl.search(ref):
                            ref = regexpiopurl.sub('DOI: 10.1088/', ref)
                        rec['refs'].append([('x', ref)])
                    print '  - ', rec['doi'], ' orcidfound:', orcidsfound
                    print '    ', rec.keys()
                    #print rec
                    if rec.has_key('autaff'):
                        if rec['autaff']:
                            recs.append(rec)
                    else:
                        if rec['auts']:
                            recs.append(rec)
    voliss.append('%s.%s' % (rec['vol'], rec['issue']))
    if not rec['vol'] in vols:
        vols.append(rec['vol'])

if len(vols) == 1:
    iopf = 'iopcrawl.' + re.sub(' ', '', jnl) + re.sub('_\d+', '', '.' + '_'.join(voliss))
else:
    iopf = 'iopcrawl.' + re.sub(' ', '', jnl) + '.' + '_'.join(voliss)

xmlf = os.path.join(xmldir,iopf+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs ,xmlfile,'IOP')
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = iopf+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()

