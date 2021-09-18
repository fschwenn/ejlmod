# -*- coding: utf-8 -*-
#harvest theses from Cologne U. 
#FS: 2019-11-25


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
import json
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
pagestocheck = 8

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Cologne U.'
jnlfilename = 'THESES-COLOGNE-%s' % (stampoftoday)


divisionsdict = {'inst_50000' : 'Universitaet zu Koeln, Faculty of Mathematics and Natural Sciences, Germany',
                 'inst_50005' : 'Universitaet zu Koeln, I. Physikalisches Institut, Zuelpicher Strasse 77, 50937 Koeln, Germany',
                 'inst_50010' : 'Universitaet zu Koeln, Institute of Physics II, Germany',
                 'inst_50015' : 'Universitaet zu Koeln, Institute of Nuclear Chemistry, Germany',
                 'inst_50050' : 'Universitaet zu Koeln, Institute for Genetics, Germany',
                 'inst_50055' : 'Universitaet zu Koeln, Institut fuer Geophysik und Meteorologie, Germany',
                 'inst_50060' : 'Universitaet zu Koeln, Institute of Computer Science, Germany',
                 'inst_50065' : 'Universitaet zu Koeln, Institute for Nuclear Physics, Germany',
                 'inst_50085' : 'Universitaet zu Koeln, Institute of Physical Chemistry, Germany',
                 'inst_50090' : 'Universitaet zu Koeln, Center for Data and Simulation Science, Germany',
                 'inst_50095' : 'Universitaet zu Koeln, Mathematical Institute, Albertus-Magnus-Platz, 50923 Koeln, Germany',
                 'inst_50110' : 'Forschungszentrum Juelich',
                 'inst_50115' : 'Universitaet zu Koeln, MPI for Plant Breeding Research, Germany',
                 'inst_50120' : 'Universitaet zu Koeln, Institut fuer Biologiedidaktik, Germany',
                 'inst_50135' : 'Universitaet zu Koeln, Institut fuer Mathematikdidaktik, Germany',
                 'inst_50140' : 'Universitaet zu Koeln, Institut fuer Physikdidaktik, Germany',
                 'inst_55110' : 'Universitaet zu Koeln, Institut fuer Geologie und Mineralogie, Germany',
                 'klips-14725' : 'Universitaet zu Koeln,  Mathematical Institute, Germany',
                 'klips-14751' : 'Universitaet zu Koeln,  Institute of Computer Science, Germany',
                 'klips-14759' : 'Universitaet zu Koeln,  Institute of Physics I, Germany',
                 'klips-14766' : 'Universitaet zu Koeln,  Institute of Physics II, Germany',
                 'klips-14774' : 'Universitaet zu Koeln,  Institute for Nuclear Physics, Germany',
                 'klips-14780' : 'Universitaet zu Koeln,  Institute for Theoretical Physics, Germany',
                 'klips-14795' : 'Universitaet zu Koeln,  Institute of Mathematics Education, Germany',
                 'klips-14801' : 'Universitaet zu Koeln,  Institute of Physics Education, Germany',
                 'klips-14722' : 'Universitaet zu Koeln,  Department of Mathematics and Computer Science, Germany',
                 'klips-14839' : 'Universitaet zu Koeln,  Institute of Physical Chemistry, Germany',
                 'klips-14859' : 'Universitaet zu Koeln,  Institute of Theoretical Chemistry, Germany',
                 'noklips-ehemalig-30040' : 'Universitaet zu Koeln,  Institut fuer Physik und ihre Didaktik, Germany',
                 'noklips-ehemalig-50015' : 'Universitaet zu Koeln,  Institute of Nuclear Chemistry, Germany',
                 'noklips-extern-50110' : ' Forschungszentrum Juelich, Germany',
                 'klips-13983' : 'Universitaet zu Koeln,  Faculty of Mathematics and Natural Sciences, Germany'}
boring = ['klips-13979', 'klips-13980', 'klips-13982', 'klips-13984', 'klips-13989', 'klips-14091',
          'klips-14092', 'klips-14094', 'klips-14132', 'klips-14134', 'klips-14138', 'klips-14139',
          'klips-14141', 'klips-14142', 'klips-14144', 'klips-14154', 'klips-14157', 'klips-14158',
          'klips-14160', 'klips-14161', 'klips-14162', 'klips-14169', 'klips-14171', 'klips-14173',
          'klips-14179', 'klips-14196', 'klips-14206', 'klips-14213', 'klips-14224', 'klips-14227',
          'klips-14235', 'klips-14245', 'klips-14249', 'klips-14250', 'klips-14251', 'klips-14254',
          'klips-14255', 'klips-14260', 'klips-14261', 'klips-14262', 'klips-14263', 'klips-14267',
          'klips-14269', 'klips-14274', 'klips-14278', 'klips-14280', 'klips-14285', 'klips-14290',
          'klips-14294', 'klips-14296', 'klips-14297', 'klips-14303', 'klips-14305', 'klips-14310',
          'klips-14311', 'klips-14315', 'klips-14317', 'klips-14321', 'klips-14324', 'klips-14332',
          'klips-14336', 'klips-14345_', 'klips-14346', 'klips-14347', 'klips-14351', 'klips-14370',
          'klips-14373', 'klips-14381', 'klips-14398', 'klips-14409', 'klips-14436', 'klips-14439',
          'klips-14443', 'klips-14445', 'klips-14448', 'klips-14461', 'klips-14462', 'klips-14467',
          'klips-14498', 'klips-14501', 'klips-14506', 'klips-14514', 'klips-14523', 'klips-14535',
          'klips-14545', 'klips-14546', 'klips-14551', 'klips-14554', 'klips-14557', 'klips-14558',
          'klips-14569', 'klips-14586', 'klips-14591', 'klips-14595', 'klips-14598', 'klips-14599',
          'klips-14600', 'klips-14634', 'klips-14652', 'klips-14661', 'klips-14662', 'klips-14682',
          'klips-14694', 'klips-14805', 'klips-14808', 'klips-14811', 'klips-14825', 'klips-14833',
          'klips-14861', 'klips-14874', 'klips-14888', 'klips-14892', 'klips-14904', 'klips-14912',
          'klips-14919', 'klips-14926', 'klips-14942', 'klips-14946', 'klips-14976', 'klips-14982',
          'klips-14986', 'klips-14989', 'klips-15006', 'klips-15019', 'klips-15053', 'klips-15076',
          'klips-15077', 'klips-15081', 'klips-15082', 'klips-15092', 'klips-15096', 'klips-15101',
          'klips-15104', 'klips-15107', 'klips-15112', 'klips-15116', 'klips-15117', 'klips-15118',
          'klips-15119', 'klips-15129', 'klips-15415', 'klips-15436', 'klips-15437', 'klips-15437',
          'klips-15454', 'klips-15454', 'klips-15641', 'klips-15662', 'klips-15663', 'klips-15946',
          'klips-16021', 'klips-16088', 'klips-16130', 'noklips-ehemalig-10030', 'noklips-ehemalig-10145',
          'noklips-ehemalig-10155', 'noklips-ehemalig-10205', 'noklips-ehemalig-10220', 'noklips-ehemalig-10',
          'noklips-ehemalig-20115', 'noklips-ehemalig-20170', 'noklips-ehemalig-30045', 'noklips-ehemalig-30050',
          'noklips-ehemalig-20200', 'noklips-ehemalig-20', 'noklips-ehemalig-30015', 'noklips-ehemalig-30020', 
          'noklips-ehemalig-30060', 'noklips-ehemalig-30075', 'noklips-ehemalig-30080', 'noklips-ehemalig-30085',
          'noklips-ehemalig-31030', 'noklips-ehemalig-35035', 'noklips-ehemalig-35060', 'noklips-ehemalig-35065',
          'noklips-ehemalig-35040', 'noklips-ehemalig-35045', 'noklips-ehemalig-35050', 'noklips-ehemalig-35055', 
          'noklips-ehemalig-35070', 'noklips-ehemalig-35', 'noklips-ehemalig-40020', 'noklips-ehemalig-40050',
          'noklips-ehemalig-40140', 'noklips-ehemalig-40145', 'noklips-extern-55120', 'noklips-extern-55125',
          'noklips-ehemalig-40', 'noklips-ehemalig-50075', 'noklips-ehemalig-55045', 'noklips-extern-50115',
          'noklips-weitere-05090', 'noklips-weitere-10025', 'noklips-weitere-10210', 'noklips-weitere-10230',
          'noklips-weitere-10325', 'noklips-weitere-10340']

                 

tocurltrunc = 'https://kups.ub.uni-koeln.de/cgi/search/archive/advanced?cache=1750151&order=-date%2Fcreators_name%2Ftitle&_action_search=1&exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Csubjects%3Asubjects%3AANY%3AEQ%3A510+530+no%7Ctype%3Atype%3AANY%3AEQ%3Athesis%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&screen=Search'
#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
#check content pages
for i in range(pagestocheck):
    tocurl = '%s&search_offset=%i' % (tocurltrunc, 20*i)
    print '---{ %i/%i }---{ %s }---' % (i+1, pagestocheck, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
    time.sleep(2)
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):        
        for a in tr.find_all('a'):
            if re.search('kups.ub.uni\-koeln.de\/\d\d', a['href']):
                trtext = tr.text
                if re.search('Bachelor thesis', trtext):
                    print ' skip Bachelor thesis'
                elif re.search('Master thesis', trtext):
                    print ' skip Master thesis'
                else:                
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'supervisor' : []}
                    rec['link'] = a['href']
                    if not re.search('PhD thesis', trtext):
                        rec['note'].append('unknown thesis type')
                    prerecs.append(rec)

#check individual thesis pages
i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.urlopen(rec['link'], context=ctx))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.open(rec['link'], context=ctx))
        except:
            print "no access to %s" % (rec['link'])
            continue
    #first get author
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.creators_name'}):
        rec['autaff'] = [[ meta['content'] ]]
    #affiliation
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.divisions'}):
        if meta['content'] in divisionsdict.keys():
            if meta['content'] in ['inst_50095', 'inst_50135', 'klips-14725', 'klips-14795']:
                rec['fc'] = 'm'
            elif meta['content'] in ['klips-14751']:
                rec['fc'] = 'c'            
            rec['autaff'][-1].append(divisionsdict[ meta['content'] ])
        else:
            #print 'unknown division', meta['content']
            rec['autaff'][-1].append('Universitaet zu Koeln, Germany')
            if meta['content'] in boring:
                keepit = False
    #get abstract
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstract'}):
        rec['abs'] = meta['content']
    #English abstract
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstracttranslated_lang'}):
        if meta['content'] == 'eng':
            for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstracttranslated'}):
                rec['abs'] = meta2['content']
    #other metadata
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #email
            if meta['name'] == 'eprints.creators_id':
                if re.search('@', meta['content']):
                    rec['autaff'][-1].append('EMAIL:%s' % (meta['content']))
            #ORCID
            elif meta['name'] == 'eprints.creators_orcid':
                orcid = re.sub('.*(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d\d).*', r'\1', meta['content']) 
                rec['autaff'][-1].append('ORCID:%s' % (orcid))
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'eprints.datestamp':
                rec['date'] = meta['content'][:10]
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] += re.split('[,;] ', meta['content'])
            #supervisor
            elif meta['name'] == 'eprints.referee_name':
                rec['supervisor'].append([meta['content'], 'Cologne U.'])
            #URN
            elif meta['name'] == 'eprints.urn':
                rec['urn'] = meta['content']
            #supervisor
            elif meta['name'] == 'eprints.referee':
                rec['supervisor'].append([meta['content'], 'Cologne U.'])
            #language
            elif meta['name'] == 'eprints.language':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
                    for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.title_translated'}):
                        rec['transtit'] = meta2['content']
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.document_url'}):
                    rec['FFT'] = meta2['content']
    #hidden PDF
    if not 'license' in rec.keys():
        for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.document_url'}):
            rec['hidden'] = meta2['content']
    #division
    for tr in artpage.body.find_all('tr'):
        tdr = ''
        for td in tr.find_all('td', attrs = {'align' : 'right'}):
            tdr = td.text.strip()
        for td in tr.find_all('td', attrs = {'valign' : 'top'}):
            if tdr == 'Divisions:':
                for a in td.find_all('a'):
                    klips = re.sub('.*\/([a-z].*)', r'\1', a['href'])
                    klips = re.sub('\/? *', '', klips)
                    if klips in boring:
                        keepit = False
                        print '  skip %s' % (td.text.strip())
                rec['note'].append('%s : %s' % (klips, td.text.strip()))
    #502
    rec['MARC'] = [('502', [('d', rec['date'][:4]), ('c', 'Cologne U.'), ('b', 'PhD')])]
    if keepit:
        print '    ', rec.keys()
#        for k in rec.keys():
#            print ' - ', k, rec[k]
        recs.append(rec)
    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


