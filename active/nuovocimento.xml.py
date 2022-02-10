# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Nuovo Cimento
# FS 2015-10-22

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
publisherdir = '/afs/desy.de/group/library/publisherdata/sif'

publisher = 'Italian Physical Society'

def xmltorec(xmlfilename):
    xmlfile = codecs.EncodedFile(open(xmlfilename, mode='rb'), 'utf8')
    xml = BeautifulSoup(''.join(xmlfile.readlines()))
    xmlfile.close()
    issrec = {'note' : [], 'auts' : [], 'aff' : [], 'refs' : []}
    #volume
    for VolumeIDStart in xml.find_all('volumeidstart'):
        issrec['vol'] = VolumeIDStart.text
    for VolumeIDEnd in xml.find_all('volumeidend'):
        if VolumeIDEnd.text != issrec['vol']:
            issrec['vol'] = '%s-%s' % (issrec['vol'], VolumeIDEnd.text)
    #issue
    for IssueIDStart in xml.find_all('issueidstart'):
        issrec['issue'] = IssueIDStart.text
    for IssueIDEnd in xml.find_all('issueidend'):
        if IssueIDEnd.text != issrec['issue']:
            issrec['issue'] = '%s-%s' % (issrec['issue'], IssueIDEnd.text)
    #date
    for CoverDate in xml.find_all('coverdate'):
        for Year in CoverDate.find_all('year'):
            issrec['date'] = Year.text
        for Month in CoverDate.find_all('month'):
            try:
                issrec['date'] = '%s-%02i' % (issrec['date'], int(Month.text))
            except:
                if re.search('\d', Month.text):
                    issrec['date'] = '%s-%02i' % (issrec['date'], int(re.sub('\D.*', '', Month.text)))
                else:
                    issrec['date'] = issrec['date']
                    break
        if re.search('\-', issrec['date']):
            for Day in CoverDate.find_all('day'):
                issrec['date'] = '%s-%02i' % (issrec['date'], int(Day.text))
    artrecs = []
    for Article in xml.find_all('article'):
        artrec = issrec.copy()
        #notes
        for ArticleInfo in Article.find_all('articleinfo'):
            if ArticleInfo.has_attr('articletype'):
                artrec['note'].append(ArticleInfo['articletype'])
        for ArticleCategory in Article.find_all('articlecategory'):
            artrec['note'].append(ArticleCategory.text)
        #DOI
        for ArticleDOI in Article.find_all('articledoi'):
            artrec['doi'] = ArticleDOI.text
        #sequence number
        for asn in Article.find_all('articlesequencenumber'):
            artrec['p1'] = asn.text
        #article ID
        for ai in Article.find_all('articleid'):
            artrec['ArticleID'] = ai.text
        #pages
        for ArticleLastPage in Article.find_all('articlelastpage'):
            p2 = ArticleLastPage.text
            if Article.find_all('articlefirstpage'):
                for ArticleFirst in Article.find_all('pagearticlefirstpage'):
                    p1 = ArticleFirst.text
                    artrec['pages'] = int(p2) - int(p1) + 1
                    if p1 != '1':
                        artrec['p1'] = p1
                        artrec['p2'] = p2
        #title
        for at in Article.find_all('articletitle'):
            artrec['tit'] = at.text
        #OA
        for mgrant in Article.find_all('metadatagrant', 
                                              attrs = {'grant' : 'OpenAccess'}):
             artrec['licence'] = {'url' : 'http://creativecommons.org/licenses/by/4.0/de/deed.en', 
                               'statement' : 'CC-BY-4.0'}
        #authors
        for AuthorGroup in Article.find_all('authorgroup'):
            for a in AuthorGroup.find_all('author'):
                ##author
                aut = ''
                for gn in a.find_all('givenname'):
                    aut += gn.text
                for fn in a.find_all('familyname'):
                    aut += ' ' + fn.text
                artrec['auts'].append(aut)
                ##her affiliation
                if a.has_attr('affiliationids'):
                    artrec['auts'].append('=' + a['affiliationids'])
        #affiliations
        for Affiliation in Article.find_all('affiliation'):
            aff = Affiliation['id'] + '= '
            for OrgName in Affiliation.find_all('orgname'):
                aff = aff + OrgName.text
            for OrgAddress in Affiliation.find_all('orgaddress'):
                for tag in OrgAddress.contents:
                    try:
                        aff = aff + ', ' + tag.text
                    except:
                        pass
            artrec['aff'].append(aff)
        #abstract
        for Abstract in Article.find_all('abstractabstract'):
            artrec['abs'] = ''
            for Para in Abstract.find_all('para'):
                artrec['abs'] += Para.text
        #PACS
        for KeywordGroup in Article.find_all('keywordgroup'):
            kwlist = []
            for Keyword in KeywordGroup.find_all('keyword'):
                kwlist.append(Keyword.text)
            for Heading in KeywordGroup.find_all('heading'):
                if Heading.text == 'PACS.':
                    artrec['pacs'] = []
                    for kw in kwlist:
                        if re.search('^\d\d\.\d\d\...', kw):
                            artrec['pacs'].append(kw[:8])
                else:
                    artrec['keyw'] = kwlist
        #references (seem to be all unstructured)
        for Citation in Article.find_all('citation'):
            ref = ''
            for cn in Citation.find_all('citationnumber'):
                ref = '[%s] ' % (cn.text)
            for bu in Citation.find_all('bibunstructured'):
                ref += '%s. '% (bu.text)
            artrec['refs'].append([('x', ref)])           
        artrecs.append(artrec)
    #journalname and type code
    for JournalInfo in xml.find_all('journalinfo'):
        for JournalTitle in JournalInfo.find_all('journaltitle'):
            for artrec in artrecs:
                if JournalTitle.text == 'Il Nuovo Cimento C':
                    artrec['jnl'] = 'Nuovo Cim.'
                    artrec['vol'] = 'C' + artrec['vol']
                    if 'ConferencePaper' in artrec['note']:
                        artrec['tc'] = 'C'
                    else:
                        artrec['tc'] = 'P'
                        fftprefix = 'ncc'
                elif JournalTitle.text == 'La Rivista del Nuovo Cimento':
                    artrec['jnl'] = 'Riv.Nuovo Cim. '
                    artrec['tc'] = 'R'
                    fftprefix = 'ncr'
                #FFT
                if artrec.has_key('licence') and artrec.has_key('ArticleID'):
                    artrec['FFT'] = 'http://prometeo.sif.it/papers/?pid=%s%s' % (fftprefix, artrec['ArticleID'])
                print '  ', artrec.keys()
    return artrecs


#read arguments
jnlfilename = sys.argv[1]
dateien = []
for sa in sys.argv[2:]:
    print sa
    dateien.append('%s/%s.xml' % (publisherdir, sa))

if not dateien:
    sys.exit(0)

#process files 
recs = []
for datei in dateien:
    recs += xmltorec(datei)

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

for datei in dateien:
    os.system('mv %s %s/done/' % (datei, publisherdir))
