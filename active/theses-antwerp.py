# -*- coding: utf-8 -*-
#harvest theses from Antwerp U.
#FS: 2022-02-11

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
import mechanize

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Antwerp U.'
rpp = 20

starturl = 'https://repository.uantwerpen.be/submit.phtml?UDses=131032129%3A24586&UDstate=1&UDmode=&UDaccess=&UDrou=%25Start:bopwexe&UDopac=opacirua&UDextra='

br = mechanize.Browser()
br.set_handle_robots(False)   # ignore robots
br.set_handle_refresh(False)  # can sometimes hang without this
br.addheaders = [('User-agent', 'Firefox')]
hdr = {'User-Agent' : 'Firefox'}

#select documents
jnlfilename = 'THESES-ANTWERP-%s' % (stampoftoday)
recs = []

response = br.open(starturl)
br.form = list(br.forms())[0]
control = br.form.find_control('FDopc_zv')
control.value = "(facultyac:a::irc.18)(pubtype:a::pt.13)"
control.size = "20"
response = br.submit()
tocpage = BeautifulSoup(response.read(), features="lxml")
recs = []
for td in tocpage.find_all('td', attrs = {'class' : 'opacshortdescriptionunit'}):
    for a in td.find_all('a'):
       if a.has_attr('href') and re.search('brocade', a['href']): 
           rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'autaff' : []}
           rec['link'] = 'https://repository.uantwerpen.be' + a['href']
           recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(2)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'].append([ meta['content'], publisher ])
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'spa':
                    rec['language'] = 'Spanish'
                elif  meta['content'] == 'dut':
                    rec['language'] = 'Dutch'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #HDL
            elif meta['name'] == 'citation_abstract_html_url':
                if re.search('hdl.handle.net', meta['content']):
                    rec['hdl'] = re.sub('.*hdl.handle.net\/', '', meta['content'])
                    rec['link'] = meta['content']
    #pages
    for span in artpage.body.find_all('span', attrs = {'class' : 'opaccatco'}):
        spant = span.text.strip()
        if re.search('\d\d', spant):
            rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', spant)
    #abs
    for span in artpage.body.find_all('span', attrs = {'class' : 'opaccatin'}):
        for script in span.find_all('script'):
            rec['abs'] = re.sub("document.write\(unpmarked\('(.*)',''\)\);", r'\1', script.string)
    #supervisor
    for span in artpage.body.find_all('span', attrs = {'class' : 'opaccatnt'}):
        for span2 in span.find_all('span', attrs = {'class' : 'opaccatntheader'}):
            if re.search('Promotor', span2.text):
                span2.decompose()
                sv = re.sub(' *\[Promotor.*', '', span.text.strip())
                sv = re.sub('^: *', '', sv)
                sv = re.sub('\n', '', sv)
                rec['supervisor'].append([sv])
    print ' ', rec.keys()
    print rec

#closing of files and printing
if recs:
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
