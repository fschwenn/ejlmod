# -*- coding: utf-8 -*-
#harvest theses from Gent
#FS: 2019-12-09


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import codecs
import datetime
import time
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Gent (main)'
jnlfilename = 'THESES-GENT-%s' % (stampoftoday)

typecode = 'T'


rpp = 20

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://biblio.ugent.be/publication?limit=' + str(rpp) + '&subject=Physics+and+Astronomy&type=dissertation'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
persdict = {}

#get details of persons
def getperson(perslink):
    print ' .  ', perslink
    try:
        perspage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(perslink))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            perspage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(perslink))
        except:
            print "no access to %s" % (rec['artlink'])
            persdict[perslink] = []
            return 
    #name
    for h1 in perspage.find_all('h1', attrs = {'itemprop' : 'name'}):
        name = re.sub('^prof. ', '', h1.text.strip())
        name = re.sub('^dr. ', '', name)
        name = re.sub('^ir. ', '', name)
        if re.search(' [vV]an ', name):
            person = [re.sub('(.*) [vV]an (.*)', r'van \2, \1', name)]
        else:
            person = [name]
    #ORCID
    (orcid, mail, address) = ('', '', '')
    for dl in perspage.body.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dd':
                dd = child.text.strip()
                #ORCID
                if re.search('^ORCID', dt):
                    orcid = 'ORCID:' + dd
                #email
                elif re.search('mail', dt):
                    for a in child.find_all('a'):
                        email = re.sub('mailto:', 'EMAIL:', a['href'])
                #address
                elif re.search('address', dt):
                    address = 'Gent U., ' + re.sub('\n', ', ', dd) + ', Belgium'                                  
            elif child.name == 'dt':
                dt = child.text.strip()
    if orcid:
        person.append(orcid)
    elif mail:
        person.append(mail)
    if address:        
        person.append(address)
    persdict[perslink] = person
    print '  . ', person
   
recs = []
for span in tocpage.body.find_all('span', attrs = {'class' : 'title'}):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : ['Vorsicht: keine Abstracts!']}
    for a in span.find_all('a'):
        rec['artlink'] = a['href']        
        recs.append(rec)
        
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']            
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    #other metadata
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            if child.name is None:
                continue

            if child.name == 'dd':
                dd = child.text.strip()
                #pages
                if re.search('Pages', dt):
                    if re.search('\d', dd):
                        rec['pages'] = re.sub('\D*(\d+).*', r'\1', dd)
                #handle
                elif re.search('Handle', dt):
                    rec['hdl'] = re.sub('.*handle.net\/', '', dd)
                #language
                elif re.search('Language', dt):
                    if not re.search('nglish', dd):
                        rec['language'] = dd
                #author
                elif re.search('Author', dt):
		            if child.find_all('a') == []:
			            author = child.text.split('\n')
                  	    if author[0] == u'':
                            author = author[1]
                    	else:
                            author = author[0]
			            rec['autaff'] = [[author]]
		            else:
                    	for a in child.find_all('a'):
                            perslink = 'https://biblio.ugent.be' + a['href']
                            if not perslink in persdict.keys():
                                getperson(perslink)
                            rec['autaff'] = [ persdict[perslink] ]
                #supervisor
                elif re.search('Promoter', dt):
                    for a in child.find_all('a'):
                        if re.search('^\/person', a['href']):
                            perslink = 'https://biblio.ugent.be' + a['href']
                            if not perslink in persdict.keys():
                                getperson(perslink)
                            rec['supervisor'].append( persdict[perslink] )
            elif child.name == 'dt':
                dt = child.text.strip()

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
