# -*- coding: utf-8 -*-
#harvest theses from Bielefeld U.
#FS: 2019-12-05


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Bielefeld (main)'

typecode = 'T'

jnlfilename = 'THESES-BIELEFELD-%s' % (stampoftoday)

numberofrecords = 200
pages = 1


prerecs = {}
for k in range(pages):
    jsonurl = 'https://pub.uni-bielefeld.de/export?cql=type%3Dbi*&cql=type%3Dbi_dissertation&fmt=json&limit=' + str(numberofrecords) + '&sort=year.desc&start=%i' % (k*numberofrecords)

    print k, jsonurl
    jfilename = '/tmp/%s.%i.json' % ( jnlfilename, k)
    if not os.path.isfile(jfilename):
        os.system('wget -q -O %s "%s"' % (jfilename, jsonurl))
        time.sleep(2)
    jfile = codecs.EncodedFile(codecs.open(jfilename, mode='rb'), 'utf8')
    jtext = ''.join(jfile.readlines())
    jfile.close()
    theses = json.loads(jtext)


    i = 0
    for thesis in theses:
        i += 1
        #print i, thesis
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : []}
        #title
        rec['tit'] = thesis['title']
        #DOI, urn
        if 'doi' in thesis.keys():
            rec['doi'] = thesis['doi']
        if 'urn' in thesis.keys():
            rec['urn'] = thesis['urn']
        else:
            rec['doi'] = '20.2000/bielefeld/' + thesis['_id']
        #license and fulltext
        if 'license' in thesis.keys():
            rec['license'] = {'url' : thesis['license']}
            if 'file' in thesis.keys():
                for datei in thesis['file']:
                    if datei['relation'] == 'main_file':
                        rec['FFT'] = 'https://pub.uni-bielefeld.de/download/%s/%s/%s' % (thesis['_id'], datei['file_id'], datei['file_name'])
        #author
        for author in thesis['author']:
            rec['autaff'].append([author['full_name']])
            if 'orcid' in author.keys():
                rec['autaff'][-1].append('ORCID:' + author['orcid'])
            rec['autaff'][-1].append(publisher)
        #supervisor
        if 'supervisor' in thesis.keys():
            for supervisor in thesis['supervisor']:
                rec['supervisor'].append([supervisor['full_name']])
                if 'orcid' in supervisor.keys():
                    rec['supervisor'][-1].append('ORCID:' + supervisor['orcid'])
        #date
        if 'defense_date' in thesis.keys():
            rec['date'] = thesis['defense_date']
        rec['year'] = thesis['year']
        #language
        if thesis['language'][0]['iso'] == 'ger':
            rec['language'] = 'german'
        #DDC
        if 'ddc' in thesis.keys():
            rec['note'] =  [ thesis['ddc'][0] ]
            if thesis['ddc'][0][:2] in ['50', '51', '52', '53']:          
                print '---{ %i/%i }---{ %i/%i }---{ %s }---' % (k, pages, i, numberofrecords, ', '.join(rec.keys()))
                prerecs[thesis['_id']] = rec

recs = []
i = 0
for tid in prerecs.keys():
    i += 1
    articlelink = 'https://pub.uni-bielefeld.de/record/' + tid
    print '---{ %i/%i }---{ %s }---' % (i, len(prerecs.keys()), articlelink)
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(articlelink))
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'DC.description'}):
        prerecs[tid]['abs'] = meta['content']
    recs.append(prerecs[tid])
    time.sleep(5)

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
