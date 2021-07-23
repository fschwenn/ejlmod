# -*- coding: utf-8 -*-
#harvest theses from Shodghanga
#FS: 2018-02-05

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
import cPickle

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# +'_special'
picklefile = '/afs/desy.de/user/l/library/dok/ejl/shodghanga.list.pickle'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Shodhganga'
pages = 2
years = 3
recsperxml = 50
server = 'shodhganga.inflibnet.ac.in'
#server = 'sg.inflibnet.ac.in'

kw = sys.argv[1]
start = int(sys.argv[2])
ende = int(sys.argv[3])


fourofour = 0
#check list of departments for physics and math
comlistlink = 'https://%s/community-list' % (server)
comlistfile = '/tmp/shodganga.community.list-%4i-%02i' % (now.year, now.month)
if not os.path.isfile(comlistfile):
    print 'downloading "%s" to "%s"' % (comlistlink, comlistfile)
    os.system('wget -O %s %s' % (comlistfile, comlistlink))
    if int(os.path.getsize(comlistfile)) <= 0:
        print '"%s" is empty :(' % (comlistfile)
        os.remove(comlistfile)        
try:
    inf = open(comlistfile, 'r')
    comlist = BeautifulSoup(''.join(inf.readlines()), features="lxml")
    inf.close()
    departments = {'Physics' : [], 'Math' : [], 'Astro' : []}
    for div in comlist.find_all('div', attrs = {'class' : 'container'}):
        for child in div.children:
            try:
                child.name
            except:
                continue
            if child.name == 'ul':
                for child2 in child.children:
                    try:
                        child2.name
                    except:
                        continue
                    if child2.name == 'li':
                        for child3 in child2.children:
                            try:
                                child3.name
                            except:
                                continue
                            if child3.name == 'div':
                                for child4 in child3.children:
                                    try:
                                        child4.name
                                    except:
                                        continue
                                    if child4.name == 'h4':
                                        for a in child4.find_all('a'):
                                            uni = a.text.strip()
                                    elif child4.name == 'ul':
                                        for li in child4.find_all('li'):
                                            for a in li.find_all('a'):
                                                hdl = re.sub('.*handle\/', '', a['href'])
                                                dep = a.text.strip()
                                                for kwt in departments.keys():
                                                    if re.search(kwt, dep, flags=re.IGNORECASE):
                                                        departments[kwt].append((hdl, uni, dep))
                                                        continue
    ouf = open(picklefile, 'w')
    cPickle.dump(departments, ouf, 2)
    ouf.close()
except:
    print 'load departments from pickle'
    inf = open(picklefile, 'r')
    departments = cPickle.load(inf)
    inf.close()
                               

recs = []
i = 0
k = 0
for (hdl, uni, dep) in departments[kw]:
    i += 1
    if i < start or i > ende:
        continue
    try:
        print '------{ %s }---{ %i/%i }---{ %s }---' % (kw, i, len(departments[kw]), uni)
    except:
        print '------{ %s }---{ %i/%i }---' % (kw, i, len(departments[kw]))
    pickedfromuni = 0
    gotall = False
    for j in range(pages):
        if gotall:
            print '   got all %s' % (nall)
            break
        tocurl = 'https://%s/handle/%s?offset=%i' % (server, hdl, j*20)            
        print '   ---{ %s }---' % (tocurl)
        nall = 0 
        try:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
            time.sleep(5)
        except:
            if not fourofour:
                try:
                    print "retry %s in 300 seconds" % (tocurl)
                    time.sleep(300)
                    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
                except:
                    print ' +++ 404 +++'
                    fourofour += 1
                    break
            else:
                print ' +++ 404 +++'
                fourofour += 1
                break
        #pick individual links            
        for tr in tocpage.body.find_all('tr'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : [], 'note' : []}
            #affiliation
            rec['aff'] = ['%s, %s, India' % (uni, dep)]
            for td in tr.find_all('td', attrs = {'headers' : 't1'}):
                #no! this is just date of the record, not of the thesis
                #rec['date'] = re.sub('\-', ' ', td.text.strip())
                #title and link
                for td2 in tr.find_all('td', attrs = {'headers' : 't2'}):   
                    rec['tit'] = td2.text.strip()
                    for a in td2.find_all('a'):                
                        rec['artlink'] = 'http://%s%s' % (server, a['href'])
                        rec['hdl'] = re.sub('.*handle\/', '',  a['href'])
                #author
                for td2 in tr.find_all('td', attrs = {'headers' : 't3'}):   
                    rec['auts'] = [ td2.text.strip() ]
                #supervisor
                for td2 in tr.find_all('td', attrs = {'headers' : 't4'}):
                    for sv in re.split(' and ', td2.text.strip()):
                        rec['supervisor'].append( [ sv ])
                ##get article page
                try:
                    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
                    time.sleep(5)
                except:
                    try:
                        print "retry %s in 180 seconds" % (rec['link'])
                        time.sleep(180)
                        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
                    except:
                        print "no access to %s" % (rec['artlink'])                            
                        continue
                for meta in artpage.head.find_all('meta'):
                    if meta.attrs.has_key('name'):
                        #pages
                        if meta['name'] == 'DCTERMS.spatial':
                            if re.search('\d', meta['content']):
                                rec['pages'] = re.sub('^\D?(\d+).*', r'\1', meta['content'])
                        #date
                        elif meta['name'] == 'DC.date':
                            if re.search('\d\d\d\d', meta['content']):
                                if re.search('[A-Za-z]+.*\d\d\d\d', meta['content']):
                                    rec['date'] = re.sub('.*(\d\d\d\d).*', r'\1',  meta['content'])
                                elif meta ['content'] == '25.11.2011':
                                    rec['date'] = '2011-11-25'
                                else:
                                    rec['date'] = meta['content']
                        #abstract
                        elif meta['name'] == 'DCTERMS.abstract':
                            if len(meta['content']) > 50:
                                rec['abs'] = meta['content']
                if not 'abs' in rec.keys():
                    rec['note'].append('Vorsicht! kein Abstract')
                #year
                if 'date' in rec.keys():
                    year = int(re.sub('.*(\d\d\d\d).*', r'\1', rec['date']))
                    if year > now.year - years:
                        recs.append(rec)
                        pickedfromuni += 1
                        if len(recs) % recsperxml == 0:
                            jnlfilename = 'THESES-SHODHGANGA-%s_%s_%02i-%i_%i-%i_%i' % (stampoftoday, kw, k, start, ende, i, len(departments[kw]))
                            #closing of files and printing
                            xmlf    = os.path.join(xmldir, jnlfilename+'.xml')
                            xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
                            ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
                            xmlfile.close()
                            #retrival
                            retfiles_text = open(retfiles_path, "r").read()
                            line = jnlfilename+'.xml'+ "\n"
                            if not line in retfiles_text:
                                retfiles = open(retfiles_path, "a")
                                retfiles.write(line)
                                retfiles.close()
                            #metarecs.append(recs)
                            recs = []
                            k += 1 
                    else:
                        print '   %i is too old' % (year)
                else:
                    rec['note'].append('kein Datum')
        #got already all
        for div in tocpage.body.find_all('div', attrs = {'class' : 'browse_range'}):
            divt = div.text.strip()
            if re.search('\d+ of \d+', divt):
                nsofar = re.sub('.* (\d+) of \d+.*', r'\1', divt)
                nall = re.sub('.* \d+ of (\d+).*', r'\1', divt)
                if nsofar == nall: gotall = True
    print '        picked %s of %s (total %s)' % (pickedfromuni, nall, len(recs))
if recs:
    if fourofour:
        jnlfilename = 'THESES-SHODHGANGA-%s_%s_%02i-%i_%i-%i_%i_fin_%isites_not_reached' % (stampoftoday, kw, k, start, ende, i, len(departments[kw]), fourofour)
    else:
        jnlfilename = 'THESES-SHODHGANGA-%s_%s_%02i-%i_%i-%i_%i_fin' % (stampoftoday, kw, k, start, ende, i, len(departments[kw]))
    #closing of files and printing
    xmlf    = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
