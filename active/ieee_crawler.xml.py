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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

absdir = '/afs/desy.de/group/library/abs'
ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

articlesperpage = 50

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

def translatejnlname(ieeename):
    if ieeename in ["Applied Superconductivity, IEEE Transactions on", "IEEE Transactions on Applied Superconductivity"]:
        jnlname = 'IEEE Trans.Appl.Supercond.'
    elif ieeename in ["Nuclear Science, IEEE Transactions on",  "IEEE Transactions on Nuclear Science"]:
        jnlname = 'IEEE Trans.Nucl.Sci.'
    elif ieeename in ["IEEE Xplore: Magnetics, IEEE Transactions on", "Magnetics, IEEE Transactions on", 'IEEE Transactions on Magnetics']:
        jnlname = 'IEEE Trans.Magnetics'
    elif ieeename in ["IEEE Xplore: Microwave Theory and Techniques, IEEE Transactions on", "IEEE Xplore: IEEE Transactions on Microwave Theory and Techniques"]:
        jnlname = 'IEEE Trans.Microwave Theor.Tech.'
    elif ieeename in ["IEEE Xplore: Plasma Science, IEEE Transactions on", "IEEE Transactions on Plasma Science"]:
        jnlname = 'IEEE Trans.Plasma Sci.'
    elif ieeename in ["IEEE Xplore: Quantum Electronics, IEEE Journal of", "IEEE Xplore: IEEE Journal of Quantum Electronics"]:
        jnlname = 'IEEE J.Quant.Electron.'
    elif ieeename in ["Instrumentation and Measurement, IEEE Transactions on", "IEEE Xplore: IEEE Transactions on Instrumentation and Measurement", "IEEE Transactions on Instrumentation and Measurement"]:
        jnlname = 'IEEE Trans.Instrum.Measur.'
    elif re.search('^IEEE Xplore . Nuclear Science Symposium Conference Record', ieeename):
        jnlname = 'IEEE Nucl.Sci.Symp.Conf.Rec.'
    elif ieeename in ["Journal of Lightwave Technology"]:
        jnlname = 'J.Lightwave Tech.'
    elif ieeename in ["IEEE Transactions on Microwave Theory and Techniques"]:
        jnlname = 'IEEE Trans.Microwave Theor.Tech.'
    elif ieeename in ["Instrumentation & Measurement Magazine, IEEE", "IEEE Instrumentation & Measurement Magazine"]:
        jnlname = 'IEEE Instrum.Measur.Mag.'
        tc = 'I'
    elif ieeename in ['IEEE Sensors Journal']:
        jnlname = 'IEEE Sensors J.'
    elif ieeename in ['IEEE Transactions on Image Processing']:
        jnlname = 'IEEE Trans.Image Process.'
    elif ieeename in ['Computing in Science & Engineering']:
        jnlname = 'Comput.Sci.Eng.'
    elif ieeename in ['IEEE Transactions on Circuits and Systems I: Regular Papers']:
        jnlname = 'IEEE Trans.Circuits Theor.'
    elif ieeename in ["IEEE Symposium Conference Record Nuclear Science 2004.",
                      "IEEE Nuclear Science Symposium Conference Record, 2005"]:
        jnlname = 'BOOK'
        tc = 'C'
    else:
        print 'unknown journal', ieeename
        sys.exit(0)
    return jnlname

def ieee(number):
    urltrunc = "http://ieeexplore.ieee.org"
    #get name of journal
    if number[0] == 'C': 
        #toclink = "/xpl/mostRecentIssue.jsp?punumber=%s&rowsPerPage=2000" % (number[1:])        
        toclink = "/xpl/conhome/%s/proceeding?rowsPerPage=%i" % (number[1:], articlesperpage)
        tc = 'C'
        jnlname = 'IEEE Nucl.Sci.Symp.Conf.Rec.'
        jnlname = 'BOOK'
    else:
        toclink = "/xpl/tocresult.jsp?isnumber=%s&rowsPerPage=%i" % (number, articlesperpage)
        tc = 'P'
        
    articlelinks = []
    driver = webdriver.PhantomJS()
    #driver = webdriver.Firefox()
    driver.implicitly_wait(30)
    #driver.delete_all_cookies()
    gotallarticles = False
    allarticlelinks = []
    notproperarticles = 0
    numberofarticles = 1000000
    i = 0
    while not gotallarticles:
        i += 1
        pagecommand = '&pageNumber=%i' % (i)
        print 'getting TOC from %s%s%s' % (urltrunc, toclink, pagecommand)        
        driver.get(urltrunc + toclink + pagecommand)
        if number[0] in ['C', '8', '9']:
#        if number[0] in ['C']:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-pdf')))
        else:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'global-content-wrapper')))
        #clicl to accept cookies
        if i == 1:
            try:
                driver.find_element_by_css_selector('.cc-btn.cc-dismiss').click()
            except:
                print "\033[0;91mCould not click .cc-btn.cc-dismiss\033[0m"
        time.sleep(3)
        page = BeautifulSoup(driver.page_source)
        if i == 1:
            for div in page.body.find_all('div', attrs = {'class' : 'Dashboard-header'}):
                divt = re.sub('[\n\t\r]', ' ', div.text.strip())
                divt = re.sub(',', '', divt)
                numberofarticles = int(re.sub('.* of +(\d+).*', r'\1', divt))
        #get links to individual articles
        articlelinks = []
        resultitems = page.body.find_all('h2', attrs = {'class' : 'result-item-title'})
        for headline in resultitems:
            links = headline.find_all('a')
            if links:
                for a in links:
                    #print a
                    #if a.text == 'View more':
                    link = a['href']
                    if not link in ['/document/8733895/']:
                        articlelinks.append(urltrunc+link)
            else:
                print ' not an article: %s' % (headline.text.strip())
                notproperarticles += 1
        if articlelinks:
            allarticlelinks += articlelinks
            print '   %i article links of %i so far (+ %i not proper articles)' % (len(allarticlelinks), numberofarticles, notproperarticles)
            if len(allarticlelinks) + notproperarticles >= numberofarticles:
                gotallarticles = True
            elif len(resultitems) < 50:
                gotallarticles = True                
        else:
            break
        time.sleep(10)

    print 'found %i article links' % (len(allarticlelinks))
    if not allarticlelinks:
        print page
    recs = []
    i = 0
    for articlelink in allarticlelinks:
        i += 1
        print '---{ %i/%i }---{ %s }---' % (i, len(allarticlelinks), articlelink)
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
        articlepage = BeautifulSoup(''.join(inf.readlines()), features="lxml")
        inf.close()
        rec = {'keyw' : [], 'autaff' : [], 'refs' : []}
        #metadata now in javascript
        for script in articlepage.find_all('script', attrs = {'type' : 'text/javascript'}):
            #if re.search('global.document.metadata', script.text):
            if script.contents and len(script.contents):
                if re.search('global.document.metadata', script.contents[0]):
                    gdm = re.sub('[\n\t]', '', script.contents[0]).strip()
                    gdm = re.sub('.*global.document.metadata=(\{.*\}).*', r'\1', gdm)
                    gdm = json.loads(gdm)
        if gdm.has_key('publicationTitle'):
            if number[0] == 'C':
                jnlname = 'BOOK'
                tc = 'C'
            else:
                jnlname = translatejnlname(gdm['publicationTitle'])
                if jnlname == 'IEEE Instrum.Measur.Mag.':
                    tc = 'I'
                elif jnlname == 'BOOK':
                    tc = 'C'
            rec['jnl'] = jnlname
        if gdm.has_key('authors'):
            for author in gdm['authors']:
                autaff = [author['name']]
                if author.has_key('affiliation'):
                    autaff += author['affiliation']
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
        else:
            rec['doi'] = '30.3000/ieee_%s_%06i' % (number, i)  
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
        rec['tc'] = tc
        if gdm['isConference']:
            rec['tc'] = 'C'
            rec['note'] = [gdm['publicationTitle']]            
        if len(args) > 1:
            rec['cnum'] = args[1]  
            rec['tc'] = 'C'
        #references
        #reffilename = '/tmp/ieee_%s.%i.ref' % (number, i)
        #if not os.path.isfile(reffilename):
        #    time.sleep(20)
        #    os.system("wget -T 300 -t 3 -q -O %s %s" % (reffilename, articlelink + 'references'))
        #inf = open(reffilename, 'r')
        #refpage = BeautifulSoup(''.join(inf.readlines()))
        #inf.close()
        try:
            driver.get(articlelink + 'references')
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'stats-reference-link-googleScholar')))
            refpage = BeautifulSoup(driver.page_source)
            for div in refpage.find_all('div', attrs = {'class' : 'reference-container'}):
                for span in div.find_all('span', attrs = {'class' : 'number'}):
                    for b in span.find_all('b'):
                        refnumber = re.sub('\.', '', span.text.strip())
                        span.replace_with('[%s] ' % (refnumber))
                for a in div.find_all('a', attrs = {'class' : 'stats-reference-link-crossRef'}):
                    rdoi = re.sub('.*doi.org\/(10.*)', r'\1', a['href'])
                    a.replace_with(', DOI: %s' % (rdoi))
                for a in div.find_all('a', attrs = {'class' : 'stats-reference-link-googleScholar'}):
                    a.replace_with('')
                ref = re.sub('[\n\t]', ' ', div.text.strip())
                ref = re.sub('  +', ' ', ref)
                rec['refs'].append([('x', ref)])
            print '  found %i references' % (len(rec['refs']))
        except:
            print '  could not load "%s%s"' % (articlelink, 'references')
            #continue
        time.sleep(11)

                    
        if jnlname == 'IEEE Nucl.Sci.Symp.Conf.Rec.':
            try:
                print '%3i/%3i %s (%s) %s, %s' % (i,len(allarticlelinks),rec['conftitle'],rec['year'],rec['doi'],rec['tit'])
            except: 
                print '%3i/%3i %s' % (i,len(allarticlelinks),rec['tit'])
        else:
            try:
                print '%3i/%3i %s %s (%s) %s, %s' % (i,len(allarticlelinks),jnlname,rec['vol'],rec['year'],rec['p1'],rec['tit'])
            except:
                print rec
        recs.append(rec)
    if jnlname == 'BOOK':
        oufname = 'IEEENuclSciSympConfRec'
    else:
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
    retfiles_text = open(retfiles_path,"r").read()
    line = outfile + "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
