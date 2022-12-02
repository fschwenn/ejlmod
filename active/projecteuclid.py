# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Project Euclid journals
# FS 2015-01-26

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
import datetime

now = datetime.datetime.now()
lastyear = now.year - 1
llastyear = now.year - 2
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

volumestodo = 5
journals = {#'aaa'   : ('Abstr.Appl.Anal. ', 'Hindawi'),
            'aihp'  : ('Ann.Inst.H.Poincare Probab.Statist.', 'Institut Henri Poincare',
                       'annales-de-linstitut-henri-poincare-probabilites-et-statistiques'),
            #'ajm'   : ('Asian J.Math.', 'International Press', 'asian-journal-of-mathematics'),
            'aop'   : ('Annals Probab.', 'The Institute of Mathematical Statistics', 'annals-of-probability'),            
            #'atmp'  : ('Adv.Theor.Math.Phys.', 'International Press'),
            'ba'    : ('Bayesian Anal.', 'International Society for Bayesian Analysis', 'bayesian-analysis'),
            'bjps'  : ('Braz.J.Probab.Statist.', 'Brazilian Statistical Association', 'brazilian-journal-of-probability-and-statistics'),
            #'cdm'   : ('Curr.Dev.Math.', 'International Press'),
            'dmj'   : ('Duke Math.J.', 'Duke University Press', 'duke-mathematical-journal'),
            'hokmj' : ('Hokkaido Math.J.', 'Hokkaido University, Department of Mathematics', 'hokkaido-mathematical-journal'),
            #'jam'   : ('J.Appl.Math.', 'Hindawi', 'journal-of-applied-mathematics'),
            'jdg'   : ('J.Diff.Geom.', 'Lehigh University', 'journal-of-differential-geometry'),
            'jgsp' : ('J.Geom.Symmetry Phys.', 'Bulgarian Academy of Sciences', 'journal-of-geometry-and-symmetry-in-physics'),
            'jmsj'  : ('J.Math.Soc.Jap.', 'Mathematical Society of Japan', 'journal-of-the-mathematical-society-of-japan'),
            #'jpm'   : ('J.Phys.Math.', 'OMICS International', 'journal-of-physical-mathematics'),
            #'maa'   : ('Methods Appl.Anal.', 'International Press'),
            'ps'    : ('Probab.Surv.', 'The Institute of Mathematical Statistics and the Bernoulli Society',
                       'probability-surveys'),
            'tjm'   : ('Tokyo J.Math.', 'Publication Committee for the Tokyo Journal of Mathematics',
                       'tokyo-journal-of-mathematics'),
            'facm'  : ('Funct.Approx.Comment.Math.', 'Adam Mickiewicz University, Faculty of Mathematics and Computer Science',
                       'functiones-et-approximatio-commentarii-mathematici'),
            'pgiq'  : ('Proc.Geom.Int.Quant.', 'Institute of Biophysics and Biomedical Engineering, Bulgarian Academy of Sciences',
                       'geometry-integrability-and-quantization')}

#journals = {'jgsp' : ('J.Geom.Symmetry Phys.', 'Bulgarian Academy of Sciences')}


jnl = sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]



def tryeucllidnumber(rec):
    if 'doi' in rec.keys():
        if re.search('^10.(4310|1214|14492|2969|3836|7169)\/[a-z]+\/\d+', rec['doi']):
            euclid = re.sub('^10.\d+\/([a-z]+)\/(\d+)', r'euclid.\1/\2', rec['doi'])
            try:
                euclidpage = BeautifulSoup(urllib2.urlopen('http://projecteuclid.org/' + euclid), features="lxml")
            except:
                print '?', 'http://projecteuclid.org/' + euclid
                return
            for meta in euclidpage.head.find_all('meta', attrs = {'name' : 'citation_doi'}):
                if meta['content'] == rec['doi']:
                    rec['MARC'] = [ ('035', [('9', 'EUCLID'), ('a', euclid)]) ]
                    print '   ->', euclid
            
    return 

recs = []
if jnl in journals.keys():
    publisher = journals[jnl][1]
    jnlname = journals[jnl][0]
    jnlfilename = 'projecteuclid_%s%s.%s' % (jnl, vol, iss)
    tocurl = 'https://projecteuclid.org/journals/%s/volume-%s/issue-%s' % (journals[jnl][2], vol, iss)
    #tocurl = 'https://projecteuclid.org/proceedings/geometry-integrability-and-quantization/Proceedings-of-the-Twenty-Second-International-Conference-on-Geometry-Integrability/toc/10.7546/giq-22-2021' #C20-06-08.6
    print '={ %s }={ %s }=' % (jnlname, tocurl)
    page = BeautifulSoup(urllib2.urlopen(tocurl), features="lxml")
    for div in page.body.find_all('div', attrs = {'class' : 'TOCLineItemRow1'}):
        for div2 in div.find_all('div', attrs = {'class' : 'row'}):
            for a in div2.find_all('a'):
                for span in a.find_all('span', attrs = {'class' : 'TOCLineItemText1'}):
                    rec = {'jnl' : jnlname, 'auts' : [], 'tc' : 'P', 'vol' : vol, 'note' : []}
                    if (jnl == 'pgiq'):
                        rec['tc'] = 'C'
                        if len(sys.argv) > 4:
                            rec['cnum'] = sys.argv[4]
                    if iss != 'none':
                        rec['issue'] = iss
                    rec['artlink'] = 'https://projecteuclid.org' + a['href']
                    rec['tit'] = span.text.strip()
                    if not rec['tit'] in ['Editorial Board', 'Table of Contents',
                                          'Front Matter', 'Back Matter', 'Preface']:
                        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink']), features="lxml")
    except:
        print "retry '%s' in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        articlepage = BeautifulSoup(urllib2.urlopen(rec['artlink']), features="lxml")
    for meta in articlepage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'dc.Date':
                rec['date'] = meta['content']
            #year
            elif meta['name'] == 'citation_year':
                rec['year'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
                elif re.search('^[a-z]+\/\d+$', meta['content']):
                    rec['MARC'] = [ ('035', [('9', 'EUCLID'), ('a', 'euclid.' + meta['content'])]) ]
                    rec['doi'] = '20.2000/ProjectEuclid/' + meta['content']
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', meta['content']))
            #abs
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split('; ', meta['content'])
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            #language
            elif meta['name'] == 'dc.Language':
                if meta['content'] != 'en':
                    if meta['content'] == 'fr':
                        rec['language'] = 'French'
                    else:
                        rec['note'].append('lang=%s' % (meta['content']))
    #license
    for a in articlepage.body.find_all('a'):
       if a.has_attr('href') and re.search('creativecommons.org', a['href']):
           rec['license'] = {'url' : a['href']}
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    #references
    refurl = rec['artlink'] + '?tab=ArticleLinkReference'
    try:
        refpage = BeautifulSoup(urllib2.urlopen(refurl), features="lxml")
    except:
        print "retry '%s' in 18 seconds" % (refurl)
        time.sleep(18)
        try:
            refpage = BeautifulSoup(urllib2.urlopen(refurl), features="lxml")
        except:
            refpage = articlepage
    for ul in refpage.body.find_all('ul', attrs = {'class' : 'ref-list'}):
        rec['refs'] = []
        for li in ul.find_all('li', attrs = {'class' : 'ref-label'}):
            for li2 in li.find_all('li', attrs = {'class' : 'googleScholar'}):
                li2.decompose()
            rec['refs'].append([('x', re.sub('[\n\t\r]', ' ', li.text.strip()))])
    print ' ', rec.keys()
    tryeucllidnumber(rec)
    #print rec
            
#write xml
if recs:
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

