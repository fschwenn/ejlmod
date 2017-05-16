# -*- coding: utf-8 -*-

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


ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
#xmldir = '/afs/desy.de/user/s/schwenn/inspire/ejl'




def spie(volumeid):
    jnlname = 'Proc.SPIE Int.Soc.Opt.Eng.'
    #jnlname = 'Proc.SPIE'
    urltrunc = "http://proceedings.spiedigitallibrary.org/"
    toclink = "volume.aspx?volumeid=%s" % (volumeid)
    print 'open %s%s' % (urltrunc, toclink)
    page = BeautifulSoup(urllib2.urlopen(urltrunc + toclink))
    #except:
    #    urltrunc = 'http://spie.org/Publications/Proceedings/'
    #    toclink = 'Volume/%s' % (volumeid)
    #    print 'open %s%s' % (urltrunc, toclink)
    #    page = BeautifulSoup(urllib2.urlopen(urltrunc + toclink))
    pageheader = page.body.find('div', attrs = {'class' : 'pageHeader'})
    spans = pageheader.find_all('span')
    volume = re.sub('Volume ','',spans[0].string.strip())
    conftitle = spans[1].string.strip()
    editors = pageheader.find('div', attrs = {'class' : 'authors'}).string.strip()
    recs = [{'tit' : conftitle, 'jnl' : jnlname, 'vol' : volume, 'tc' : 'K'}]
    recs[0]['auts'] = [ejlmod2.shapeaut(editor)+' (Ed.)' for editor in re.split('; ',editors)]
    print jnlname,volume
    for div in page.body.find_all('div'):
        if div.attrs.has_key('class'):
            if 'articleType' in div['class']:
                articletype = div.find('a').string
            elif 'articleContent' in div['class'] and not re.search('^Front Matter', articletype):
                rec = {'keyw' : [], 'note' : [articletype], 'jnl' : jnlname, 'vol' : volume, 'auts' : [], 'tc' : 'C', 'aff' : [], 'refs' : []}
                tempauts = []
                link = div.find('a', attrs = {'class' : 'relatedArticle'})['href']
                print '  open %s%s' % (urltrunc, link)
                time.sleep(10)
                try:
                    articlepage = BeautifulSoup(urllib2.urlopen(urltrunc +link, timeout=300))
                except:
                    print 'retry %s in 5 minutes' % (urltrunc +link)
                    time.sleep(300)
                    try:
                        articlepage = BeautifulSoup(urllib2.urlopen(urltrunc +link, timeout=300))
                    except:
                        print 'could not get metadata for %s' % (link)
                        continue
                for abstract in articlepage.body.find_all('span', attrs = {'class' : 'Abstract'}):
                    try:
                        rec['abs'] = abstract.string
                    except:
                        for para in abstract.find_all('p', attrs = {'class' : 'para'}):
                            rec['abs'] = para.string
                (affsofaut, autsofaff) = ({}, {})
                for meta in articlepage.head.find_all('meta'):
                    if 'citation_title' in meta['name']:
                        rec['tit'] = meta['content']
                    elif 'citation_firstpage' in meta['name']:
                        rec['p1'] = meta['content']
                    elif 'citation_lastpage' in meta['name']:
                        #rec['p2'] = meta['content']
                        rec['pages'] = re.sub('.*\-','',meta['content'])
                    elif 'citation_doi' in meta['name']:
                        rec['doi'] = meta['content']
                    elif 'citation_keyword' in meta['name']:
                        rec['keyw'].append(meta['content'])
                    elif 'citation_publication_date' in meta['name']:
                        rec['date'] = meta['content']
                        rec['year'] = rec['date'][:4]
                    elif 'pdf' in meta['name']:
                        for OA in div.find_all('img', attrs = {'src' : 'Images/icons/icon_openaccess.png'}):
                            rec['pdf'] = meta['content']
                    elif 'citation_author_institution' in meta['name']:
                        affsofaut[tempauts[-1]].append(meta['content'])
                        if autsofaff.has_key(meta['content']):
                            autsofaff[meta['content']][0].append(tempauts[-1])
                        else:
                            autsofaff[meta['content']] = [[tempauts[-1]],len(autsofaff)+1]
                    elif 'citation_author' in meta['name']:
                        tempauts.append(meta['content'])
                        affsofaut[tempauts[-1]] = []
                #for div in articlepage.find_all('div', attrs = {'class' : 'refContent'}):
                #    rec['refs'].append([('x', div.text)])
                if len(args) > 1:
                    rec['cnum'] = args[1]

                #print autsofaff
                #print affsofaut

                for aut in tempauts:
                    rec['auts'].append(ejlmod2.shapeaut(aut))
                    for  aff in affsofaut[aut]:
                        rec['auts'].append('=Aff%s' % autsofaff[aff][1])
                for tupel in sorted([(int(autsofaff[aff][1]),aff) for aff in autsofaff]):
                    rec['aff'].append('Aff%i= %s' % (tupel[0],tupel[1]))
                if rec.has_key('year'):
                    print '%s %s (%s) %s, %s' % (jnlname,volume,rec['year'],rec['p1'],rec['tit'])
                    recs.append(rec)
                else:
                    print '=== PROBLEM WITH RECORD ==='
                    print rec
                    print '==========================='

    recs[0]['year'] = rec['year']
    if len(args) > 2:
        recs[0]['cnum'] = args[2]
    return recs




if __name__ == '__main__':
    usage = """
        python spie_proc_crawler.py volumeid [cnum]
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) > 2:
            raise getopt.GetoptError("Too many arguments given!!!")
        elif not args:
            raise getopt.GetoptError("Missing mandatory argument volumeid")
    except getopt.GetoptError as err:
        print(str(err))  # will print something like "option -a not recognized"
        print(usage)
        sys.exit(2)
    volumeid = args[0]
    publisher = 'International Society for Optics and Photonics'
    recs = spie(volumeid)
    rvolumeid = recs[0]['vol']
    if len(args) > 1:
        cnum = args[1]
        outfile = 'spie%s_%s.xml' % (rvolumeid, cnum)
    else:
        outfile = 'spie%s.xml' % (rvolumeid)
    #dokf = codecs.EncodedFile(open(os.path.join(xmldir,outfile),mode='wb'),"utf8")
    dokf = open(os.path.join(xmldir,outfile),'w')
    ejlmod2.writeXML(recs,dokf,publisher)
    dokf.close()
    #retrival
    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
    retfiles_text = open(retfiles_path,"r").read()
    line = outfile+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
