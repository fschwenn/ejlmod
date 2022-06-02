# -*- coding: utf-8 -*-
#harvest theses (with english titles) from Tokyo U.
#FS: 2020-06-22

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startdate = now + datetime.timedelta(days=-190)
stampofstartdate = '%4d-%02d-%02d' % (startdate.year, startdate.month, startdate.day)


publisher = 'Tokyo U. '

jnlfilename = 'THESES-TOKYO_U-%s' % (stampoftoday)


hdr = {'User-Agent' : 'Magic Browser'}

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()


tocurl = 'https://repository.dl.itc.u-tokyo.ac.jp/oai?verb=ListIdentifiers&metadataPrefix=oai_dc&from=' + stampofstartdate
prerecs = []
notcomplete = True
cls = 0
i = 0
while notcomplete:
    i += 1
    print tocurl
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for identifier in tocpage.find_all('identifier'):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'identifier' : identifier.text.strip(), 'note' : []}
        rec['artlink'] = 'https://repository.dl.itc.u-tokyo.ac.jp/records/' + re.sub('.*:0*', '', rec['identifier'])
        if not rec['identifier'] in uninterestingDOIS:
            prerecs.append(rec)
    notcomplete = False
    for rt in tocpage.find_all('resumptiontoken'):
        tocurl = 'https://repository.dl.itc.u-tokyo.ac.jp/oai?verb=ListIdentifiers&resumptionToken=' + rt.text.strip()
        cls = int(rt['completelistsize'])
        notcomplete = True
    if prerecs:
        print prerecs[-1]['identifier']
    print '[%i] %i/%i/%i' % (i, len(prerecs), 100*i, cls)
    if 100*i >= cls:
        notcomplete = False
    time.sleep(2)


i = 0
recs = []
newlydone = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
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
    try:
        artpage.body.find_all('ol', attrs = {'class' : 'breadcrumb'})
        newlydone.append(rec['identifier'])
    except:
        continue
    #check relevance    
    keepit = True
    ols = artpage.body.find_all('ol', attrs = {'class' : 'breadcrumb'})
    lis = ols[0].find_all('a')
    #faculty
    fac = re.sub('\D', '', lis[0].text.strip())
    if fac in ['110', '111', '112', '113', '114',
               '116', '117', '118', '119', '120',
               '122', '123', '124', '131', '132', '133', '134', '135', '136',
               '138', '139', '140', '156', '166', '181', '182', '190', '191', '192', '200', '300']:
        print ' skip fac=%s' % (fac)
        keepit = False
    else:
        rec['note'].append('fac='+fac)
    if keepit:
        #department
        dep = re.sub('\D', '', lis[1].text.strip())
        if dep in ['06', '09', '11', '14', '32', '46']:
            print 'skip dep=%s' % (dep)
            keepit = False
        else:
            rec['note'].append('dep='+dep)
        #documeny type
        if len(ols) > 1:
            lis = ols[1].find_all('a')
            if len(lis) > 2:
                deg = re.sub('\D', '', lis[2].text.strip())
                if deg != '021':
                    print ' skip deg=%s' % (deg)
                    keepit = False
            else:
                keepit = False
    #find JSON
    if keepit:
        for pre in artpage.body.find_all('pre', attrs = {'class' : 'hide'}):
            metadata = json.loads(pre.text)
            print ' keys:', metadata.keys()
            #title
            rec['tit'] = metadata['item_title']
            if not re.search('[a-zA-Z]', rec['tit']):
                print ' skip theses with Japanes title'
                keepit = False
            #date
            rec['date'] = metadata['publish_date']
            if 'item_7_biblio_info_7' in metadata.keys():
                rec['date'] = metadata['item_7_biblio_info_7']['attribute_value_mlt'][0]['bibliographicIssueDates']['bibliographicIssueDate']
            #DOI
            if re.search('doi.org', metadata['permalink_uri']):
                rec['doi'] = re.sub('.*org\/', '', metadata['permalink_uri'])
            elif re.search('handle.net', metadata['permalink_uri']):
                rec['hdl'] = re.sub('.*handle.net\/', '', metadata['permalink_uri'])
            else:
                rec['doi'] = '20.2000/TokyoU/' + re.sub('\W', '', metadata['permalink_uri'])
            #author
            if 'item_7_full_name_3' in metadata.keys():
                rec['autaff'] = [[ metadata['item_7_full_name_3']['attribute_value_mlt'][0]['names'][0]['name'], publisher ]]
            else:
                for a in artpage.body.find_all('a', attrs = {'class' : 'creator-name'}):
                    rec['autaff'] = [[ a.text.strip(), publisher ]]
            #language
            if 'item_language' in metadata.keys():
                lang = metadata['item_language']['attribute_value_mlt'][0]['subitem_language']
                if lang == 'jpn':
                    rec['language'] = 'Japanese'
            #abstract
            if 'item_4_description_5' in metadata.keys():
                rec['abs'] = metadata['item_4_description_5']['attribute_value_mlt'][0]['subitem_description']
    if keepit:
        recs.append(rec)
        print rec
    else:
        newuninterestingDOIS.append(rec['identifier'])

jnlfilename = 'THESES-TOKYO_U-%sB' % (stampoftoday)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
