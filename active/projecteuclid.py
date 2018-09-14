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
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

volumestodo = 5
journals = {#'aaa'   : ('Abstr.Appl.Anal. ', 'Hindawi'),
            'aihp'  : ('Ann.Inst.H.Poincare Probab.Statist.', 'Institut Henri Poincare'),
            'ajm'   : ('Asian J.Math.', 'International Press'),
            'aop'   : ('Annals Probab.', 'The Institute of Mathematical Statistics'),            
            #'atmp'  : ('Adv.Theor.Math.Phys.', 'International Press'),
            'ba'    : ('Bayesian Anal.', 'International Society for Bayesian Analysis'),
            'bjps'  : ('Braz.J.Probab.Statist.', 'Brazilian Statistical Association'),
            #'cdm'   : ('Curr.Dev.Math.', 'International Press'),
            'dmj'   : ('Duke Math.J.', 'Duke University Press'),
            'hokmj' : ('Hokkaido Math.J.', 'Hokkaido University, Department of Mathematics'),
            #'jam'   : ('J.Appl.Math.', 'Hindawi'),
            'jdg'   : ('J.Diff.Geom.', 'Lehigh University'),
            'jmsj'  : ('J.Math.Soc.Jap.', 'Mathematical Society of Japan'),
            'jpm'   : ('J.Phys.Math.', 'OMICS International'),
            #'maa'   : ('Methods Appl.Anal.', 'International Press'),
            'ps'    : ('Probab.Surv.', 'The Institute of Mathematical Statistics and the Bernoulli Society'),
            'tjm'   : ('Tokyo J.Math.', 'Publication Committee for the Tokyo Journal of Mathematics'),
            'facm'  : ('Funct.Approx.Comment.Math.', 'Adam Mickiewicz University, Faculty of Mathematics and Computer Science'),
            'pgiq'  : ('Proc.Geom.Int.Quant.', 'Institute of Biophysics and Biomedical Engineering, Bulgarian Academy of Sciences')}

#journals = {'jdg'   : ('J.Diff.Geom.', 'Lehigh University')}


temp = {'pgiq' : ['https://projecteuclid.org/euclid.pgiq/1484362813']}


for jnl in journals.keys():
#for jnl in temp.keys():

    print jnl
#    print todo
    jnlname = journals[jnl][0]
    publisher = journals[jnl][1]
    #all issues page
    print jnlname
    url = 'http://projecteuclid.org/all/euclid.%s' % (jnl)
    page = BeautifulSoup(urllib2.urlopen(url))
    todo = []
    for ul in page.body.find_all('ul', attrs = {'class' : 'contents-simple'}):
        for a in ul.find_all('a'):
            if a.has_attr('href'):
                link = 'http://projecteuclid.org' + a['href']
                text = a.text.strip()
                if len(todo) < volumestodo:
                    todo.append(link)
                    print ' ',re.sub('\n? +', ' ', text)
                else:
                    break
    #todo = temp[jnl]
    #individual volumes
    for link in todo:
        jnlfilename = re.sub('.*euclid.(.*?)\/(.*)', r'projecteuclid_\1.\2', link)
        #check whether file already exists
        goahead = True
        for ordner in ['/', '/zu_punkten/', '/zu_punkten/enriched/', 
                       '/backup/', '/backup/%i/' % (lastyear), 
                       '/backup/%i/' % (llastyear), '/onhold/']:
            if os.path.isfile(ejldir + ordner + jnlfilename + '.doki'):
                print '    Datei %s exisitiert bereit in %s' % (jnlfilename, ordner)
                goahead = False
        if not goahead:
            continue
        print '   ', jnlfilename
        tocpage = BeautifulSoup(urllib2.urlopen(link))
        #volume metadata
        for div in tocpage.body.find_all('div', attrs = {'class' : 'publication'}):
            for h3 in div.find_all('h3'):
                note = re.sub('[\n\t]', ' ', h3.text)
                note = re.sub('  +', ' ', note.strip())
                break
        for p in tocpage.body.find_all('p', attrs = {'class' : 'date'}):
            date = p.text
        #make list of article links
        articles = []
        for span in tocpage.body.find_all('span', attrs = {'class' : 'title'}):
            for a in span.find_all('a'):
                articles.append(a['href'])
        #print articles
        recs = []
        for article in articles:
            #rec = {'jnl' : jnlname, 'link' : 'http://projecteuclid.org'+article, 'auts' : [], 'tc' : 'P'}
            rec = {'jnl' : jnlname, 'auts' : [], 'tc' : 'P'}
            if jnl == 'pgiq':
                rec['tc'] = 'C'
            rec['note'] = [ note ]
            try:
                articlepage = BeautifulSoup(urllib2.urlopen('http://projecteuclid.org' + article))
            except:
                print "retry '%s' in 180 seconds" % ('http://projecteuclid.org' + article)
                time.sleep(180)
                articlepage = BeautifulSoup(urllib2.urlopen('http://projecteuclid.org' + article))
            #pages
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_date'}):
                rec['date'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_year'}):
                rec['year'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_volume'}):
                rec['vol'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_issue'}):
                rec['issue'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_firstpage'}):
                rec['p1'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_lastpage'}):
                rec['p2'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_author'}):
                rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', meta['content']))
            #doi
            rec['doi'] = '20.2000' + article
            for div in articlepage.body.find_all('div', attrs = {'id' : 'info'}):
                for p in div.find_all('p'):
                    ptext = p.text.strip()
                    if re.search('Digital Object Identifier.*10\.....\/', ptext):
                        rec['doi'] = re.sub('.*doi: *(10\..*)', r'\1', ptext)
            #title
            for section in articlepage.body.find_all('section', attrs = {'class' : 'publication-content'}):
                rec['tit'] = section.find('h3').text
            #abstract 
            for div in articlepage.body.find_all('div', attrs = {'class' : 'abstract-text'}):
                rec['abs'] = re.sub('[\t\n]', '', div.text)
            #references
            for ul in articlepage.body.find_all('ul', attrs = {'class' : 'references'}):
                rec['refs'] = []
                for li in ul.find_all('li'):
                    rec['refs'].append([('x', li.text)])
            print '        ', rec['doi']
            year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
            if year >= now.year - 1:
                recs.append(rec)
        #write xml
        if recs:
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

