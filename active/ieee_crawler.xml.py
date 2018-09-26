# -*- coding: utf-8 -*-
#new 15.11.16

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import time
import json

absdir = '/afs/desy.de/group/library/abs'
ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
#xmldir = '/afs/desy.de/user/s/schwenn/inspire/ejl'
#xmldir = '/scratch/schwenn'


def meta_with_name(tag):
    return tag.name == 'meta' and tag.has_attr('name')
    
def fsunwrap(tag):
    try: 
        for i in tag.find_all('i'):
            cont = i.string
            i.replace_with(cont)
    except:
        print 'fsunwrap-i-problem'
    try: 
        for b in tag.find_all('b'):
            cont = b.string
            b.replace_with(cont)
    except:
        print 'fsunwrap-b-problem'
    try: 
        for sup in tag.find_all('sup'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('sub'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    try: 
        for form in tag.find_all('formula',attrs={'formulatype': 'inline'}):
            form.replace_with(' [FORMULA] ')
    except:
        print 'fsunwrap-form-problem'
    return tag

def referencetostring(reference):
    refstring = re.sub('\s+',' ',fsunwrap(reference).prettify())
    refstring = re.sub('<li> *(.*) *<br.*',r'\1',refstring)
    for a in reference.find_all('a'):
        if a.has_attr('href') and re.search('dx.doi.org\/',a['href']):
            refstring += ', doi: %s' % (re.sub('.*dx.doi.org\/','',a['href']))
    return refstring

def ieee(number):
    urltrunc = "http://ieeexplore.ieee.org"
    #get name of journal
    if number[0] == 'C':
        toclink = "/xpl/mostRecentIssue.jsp?punumber=%s&rowsPerPage=2000" % (number[1:])
        tc = 'C'
        jnlname = 'IEEE Nucl.Sci.Symp.Conf.Rec.'
        jnlname = 'BOOK'
    else:
        toclink = "/xpl/tocresult.jsp?isnumber=%s&rowsPerPage=2000" % (number)
        tc = 'P'
    print 'getting TOC from %s%s' % (urltrunc, toclink)
    page = BeautifulSoup(urllib2.urlopen(urltrunc + toclink,timeout=300))
    for meta in page.head.find_all('meta'):
        fsunwrap(meta)
        if meta.attrs.has_key('name') and 'Title' in meta['name']:
            if meta['content'] in ["IEEE Xplore - Applied Superconductivity, IEEE Transactions on", "IEEE Xplore - IEEE Transactions on Applied Superconductivity"]:
                jnlname = 'IEEE Trans.Appl.Supercond.'
            elif meta['content'] in ["IEEE Xplore - Nuclear Science, IEEE Transactions on",  "IEEE Xplore - IEEE Transactions on Nuclear Science"]:
                jnlname = 'IEEE Trans.Nucl.Sci.'
            elif meta['content'] in ["IEEE Xplore: Magnetics, IEEE Transactions on", "IEEE Xplore - Magnetics, IEEE Transactions on", 'IEEE Xplore - IEEE Transactions on Magnetics']:
                jnlname = 'IEEE Trans.Magnetics'
            elif meta['content'] in ["IEEE Xplore: Microwave Theory and Techniques, IEEE Transactions on", "IEEE Xplore: IEEE Transactions on Microwave Theory and Techniques"]:
                jnlname = 'IEEE Trans.Microwave Theor.Tech.'
            elif meta['content'] in ["IEEE Xplore: Plasma Science, IEEE Transactions on", "IEEE Xplore: "]:
                jnlname = 'IEEE Trans.Plasma Sci.'
            elif meta['content'] in ["IEEE Xplore: Quantum Electronics, IEEE Journal of", "IEEE Xplore: IEEE Journal of Quantum Electronics"]:
                jnlname = 'IEEE J.Quant.Electron.'
            elif meta['content'] in ["IEEE Xplore - Instrumentation and Measurement, IEEE Transactions on", "IEEE Xplore: IEEE Transactions on Instrumentation and Measurement", "IEEE Xplore - IEEE Transactions on Instrumentation and Measurement"]:
                jnlname = 'IEEE Trans.Instrum.Measur.'
            elif re.search('^IEEE Xplore . Nuclear Science Symposium Conference Record', meta['content']):
                jnlname = 'IEEE Nucl.Sci.Symp.Conf.Rec.'
            elif meta['content'] in ["IEEE Xplore - Journal of Lightwave Technology"]:
                jnlname = 'J.Lightwave Tech.'
            elif meta['content'] in ["IEEE Xplore - Instrumentation & Measurement Magazine, IEEE", "IEEE Xplore - IEEE Instrumentation & Measurement Magazine"]:
                jnlname = 'IEEE Instrum.Measur.Mag.'
                tc = 'I'
            elif meta['content'] in ["IEEE Xplore - IEEE Symposium Conference Record Nuclear Science 2004.",
                                     "IEEE Xplore - IEEE Nuclear Science Symposium Conference Record, 2005"]:
                jnlname = 'BOOK'
                tc = 'C'
            else:
                print 'unknown journal',meta['content']
                sys.exit(0)
    #get links to individual articles
    articlelinks = []
    for a in page.body.find_all('a', attrs = {'class' : 'art-abs-url'}):
        if a.attrs.has_key('href'):
            link = a['href']
            articlelinks.append(urltrunc+link)
    recs = []
    i = 0
    for articlelink in articlelinks:
        i += 1
        print 'articlelink:', articlelink
        rec = {'keyw' : [], 'jnl' : jnlname, 'autaff' : [], 'tc' : tc}
        #rec['note'] = ['Konferenz ?']
        artfilename = '/tmp/ieee_%s.%i' % (number, i)
        if not os.path.isfile(artfilename):
            time.sleep(10)
            try:
                os.system("wget -T 300 -t 3 -q -O %s %s" % (artfilename, articlelink))
            except:
                print "retry in 600 seconds"
                time.sleep(60)
        inf = open(artfilename, 'r')
        articlepage = BeautifulSoup(''.join(inf.readlines()))

#        try:
#            articlepage = BeautifulSoup(urllib2.urlopen(articlelink,timeout=300))
#        except:
#            try:
#                print "retry in 60 seconds"
#                time.sleep(60)
#                articlepage = BeautifulSoup(urllib2.urlopen(articlelink,timeout=300))
#            except:
#                print "retry in 600 seconds"
#                time.sleep(600)
#                articlepage = BeautifulSoup(urllib2.urlopen(articlelink,timeout=300))                
        #metadata now in javascript
        for script in articlepage.find_all('script', attrs = {'type' : 'text/javascript'}):
            if re.search('global.document.metadata', script.text):
                gdm = re.sub('[\n\t]', '', script.text).strip()
                gdm = re.sub('.*global.document.metadata=(\{.*\}).*', r'\1', gdm)
                gdm = json.loads(gdm)
        if gdm.has_key('authors'):
            for author in gdm['authors']:
                autaff = [author['name']]
                if author.has_key('affiliation'):
                    autaff.append(author['affiliation'])
                if author.has_key('orcid'):
                    autaff.append('ORCID:'+author['orcid'])
                rec['autaff'].append(autaff)
        if jnlname in ['IEEE Trans.Magnetics', 'IEEE Trans.Appl.Supercond.']:
            if gdm.has_key('externalId'):
                rec['p1'] = gdm['externalId']
            elif gdm.has_key('articleNumber'):
                rec['p1'] = gdm['articleNumber']
            else:
                rec['p1'] = gdm['startPage']
                rec['p2'] = gdm['endPage']
        else:
#            if gdm.has_key('endPageXXX'):
            if gdm.has_key('endPage'):
                rec['p1'] = gdm['startPage']
                rec['p2'] = gdm['endPage']
            elif gdm.has_key('externalId'):
                rec['p1'] = gdm['externalId']
            else:
                rec['p1'] = gdm['articleNumber']
        if gdm['isFreeDocument']:
            rec['FFT'] = urltrunc + gdm['pdfPath']
        rec['tit'] = gdm['formulaStrippedArticleTitle']
        if gdm.has_key('abstract'):
            rec['abs'] = gdm['abstract']
        ## mistake in metadata
        if re.search('\d+ pp', gdm['startPage']):
            rec['pages'] = re.sub(' .*', '', gdm['startPage'])
            rec['p1'] = str(int(gdm['endPage']) - int(rec['pages']) + 1)            
        else:
            try:
                rec['pages'] = int(re.sub(' .*', '', gdm['endPage'])) - int(gdm['startPage']) + 1
            except:
                pass
        if gdm.has_key('doi'):
            rec['doi'] = gdm['doi']
        if gdm.has_key('keywords'):
            for kws in gdm['keywords']:
                for kw in kws['kwd']:
                    if not kw in rec['keyw']:
                        rec['keyw'].append(kw)
        try:
            rec['date'] = gdm['journalDisplayDateOfPublication']
        except:
            rec['date'] = gdm['publicationDate']
        rec['year'] = rec['date'][-4:]
        if gdm.has_key('issue'):
            rec['issue'] = gdm['issue']
        if gdm.has_key('volume'):
            rec['vol'] = gdm['volume']
        if gdm['isConference']:
            rec['tc'] = 'C'
            rec['note'] = [gdm['publicationTitle']]
        if len(args) > 1:
            rec['cnum'] = args[1]  
            rec['tc'] = 'C'
        #references
        #now hidden in JavaScript
                    
        if jnlname == 'IEEE Nucl.Sci.Symp.Conf.Rec.':
            try:
                print '%3i/%3i %s (%s) %s, %s' % (i,len(articlelinks),rec['conftitle'],rec['year'],rec['doi'],rec['tit'])
            except: 
                print '%3i/%3i %s' % (i,len(articlelinks),rec['tit'])
        else:
            try:
                print '%3i/%3i %s %s (%s) %s, %s' % (i,len(articlelinks),jnlname,rec['vol'],rec['year'],rec['p1'],rec['tit'])
            except:
                print rec
        recs.append(rec)
        
    oufname = re.sub('[ \.]','',jnlname).lower()
    if rec.has_key('vol'): oufname += '.'+rec['vol']
    if rec.has_key('issue'): oufname += '.'+rec['issue']
    if rec.has_key('cnum'): oufname += '.'+rec['cnum']
    return (recs, oufname+'_'+number+'.xml')


if __name__ == '__main__':
    usage = """
        python ieee_crawler.py Cpunumber|isnumber [cnum]
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) > 3:
            raise getopt.GetoptError("Too many arguments given!!!")
        elif not args:
            raise getopt.GetoptError("Missing mandatory argument number")
    except getopt.GetoptError as err:
        print(str(err))  # will print something like "option -a not recognized"
        print(usage)
        sys.exit(2)
    number = args[0]
    publisher = 'IEEE'

    (recs,outfile) = ieee(number)
    dokf = open(os.path.join(xmldir,outfile),'w')
    ejlmod2.writeXML(recs,dokf,publisher)
    dokf.close()

#os.system('rm /tmp/ieee_%s*' % (number))

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = outfile + "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
