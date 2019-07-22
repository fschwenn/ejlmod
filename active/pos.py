#!/usr/bin/python
import re
import os
import sys
import datetime
import getopt
import codecs
from invenio.bibrecord import *
import urllib2
import urlparse
from bs4 import BeautifulSoup

from collclean_lib import coll_cleanforthe
from collclean_lib import coll_clean710
from collclean_lib import coll_split

retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
ftppath = '/afs/desy.de/group/library/preprints/incoming/'
publisherpath = '/afs/desy.de/group/library/publisherdata/sissa/done/'
xmlpath = '/afs/desy.de/user/l/library/inspire/ejl/'
tmpdir = '/afs/desy.de/user/l/library/tmp/'
pdftmpdir = '/afs/desy.de/user/l/library/tmp/pos/'
bibclassifycommand = 'python /afs/desy.de/user/l/library/proc/bibclassify/bibclassify_cli.py -n10 -s -k /afs/desy.de/user/l/library/akw/HEPont.rdf '
antibibclassifycommand = 'python /afs/desy.de/user/l/library/proc/bibclassify/bibclassify_cli.py -n10 -s -k /afs/desy.de/user/l/library/akw/antiHEPont.rdf '


def pos_harvesting(conf_acronym,cnum):
    #FS: there can be spaces in PoS-Conf-Acronyms which cause problems in other programs like retinspire.pl
    cat = re.sub(' ', '_', conf_acronym)
    cnum = re.sub('/','-',cnum.upper())
    appendrecs = []
    message = 'Processing %s with %s\n' % (conf_acronym, cnum)

    publicationyear = 1
    publicationyearchanged = False
    
    bigxmlfile = codecs.EncodedFile(codecs.open(xmlpath+'pos_'+cat+'.xml',mode='wb'),'utf8')
    bigxmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n')
    restxmlfile = codecs.EncodedFile(codecs.open(xmlpath+'pos_'+cat+'.merges.xml',mode='wb'),'utf8')
    restxmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n')

    xmlfiles = os.listdir(ftppath + conf_acronym)
    message = '%s %i records\n' % (message,len(xmlfiles))
    
    records = []
    counter = 0
    for datei in xmlfiles:
        counter += 1
        print '---{ %s }---{ %i/%i }---------' % (datei, counter, len(xmlfiles))
        xmlfile = codecs.EncodedFile(codecs.open(ftppath + conf_acronym + '/' + datei, mode='rb'),'utf8')
        recs = create_records(xmlfile.read(),verbose=1)
        xmlfile.close()
        for recordtuple in recs:
            if recordtuple[1] == 0:
                message = '%sBad record %s\n' % (message,recordtuple[2])
                print message
                continue
            record = recordtuple[0]
            if not record:
                continue        

                            
            
            if record.has_key('540'):
                m540 = record_delete_field(record,'540',' ',' ')
                for field in m540[0][0]:
                    if field[0] == 'a':
                        ft= re.sub('.*(CC.*0).*',  r'\1', field[1])
                        ft = re.sub(' ',  '-', ft)
                        record_add_field(record, '540', ' ', ' ', '', [('a', ft), ('b','SISSA')])
            
            article_id = None
            if record.has_key('773'):
                m773 = record_delete_field(record,'773',' ',' ')
                for entry in m773[0][0]:
                    if entry[0] == 'y' and int(entry[1]) > publicationyear:
                        if publicationyear > 1:
                            publicationyearchanged = True
                        publicationyear = int(entry[1]) 
                        print 'publicationyear =', publicationyear, publicationyearchanged
            else: 
                if record.has_key('001'):
                    m001 = record_get_field_values(record,'001')
                    appendrecs.append(m001[0])
                    restxmlfile.write(record_xml_output(record))
                    restxmlfile.write('\n')
                else:
                    print 'Error: bad record\n',record
                continue
            for (i,v) in m773[0][0]:
                if i == 'c':
                    article_id = v
            m773[0][0].append(('w',cnum))
            record_add_fields(record,'773',m773)
            nodoi = 'pos.%s.%s' % (cat,article_id)
            doi1 = re.sub('[\(\)\/]', '_', nodoi)
            #record_add_field(record,'024','7',' ','',[('a',nodoi),('2','NODOI')])
            #extract title from PDF            
            if record.has_key('856'):
                for entry in record['856'][0][0]:
                    if entry[0] == 'u':
                        pdflink = entry[1]
            else:
                print record
                print '--- NO LINK ---'
                continue
            posfile = '%s%s' % (pdftmpdir, re.sub('.*\/', '', pdflink[:-4]))
            if not os.path.isfile(posfile + '.pdf'):
                print ' download %s to %s.pdf' % (pdflink, posfile)
                os.system('wget -O %s.pdf %s' % (posfile, pdflink))
                os.system('pdftotext %s.pdf' % (posfile))
            try:
                inf = open('%s.txt' % (posfile), 'r')
                lines = inf.readlines()
                inf.close()
                pdftitle = lines[0].strip()
                if pdftitle[:3] == 'PoS':
                    pdftitle = lines[2].strip()
                title = record['245'][0][0][0][1]
                if pdftitle and title != pdftitle:
                    record_add_field(record, '246', ' ', ' ', '', [('a', pdftitle), ('9', 'SISSA')]) 
                #record_add_field(record, '246', ' ', ' ', '', [('a', title), ('9', 'SISSA')]) 
            except:
                print 'could not extract informations from PDF'
            #get more information from the web page
            (doi, abstract) = (False, False)
            metaurl = re.sub('.*\/(\d+\/\d+).*', r'https://pos.sissa.it/\1', pdflink)
            print '-[%s]-' % (metaurl)
            metapage = BeautifulSoup(urllib2.urlopen(metaurl))
            for meta in metapage.find_all('meta', attrs = {'name' : 'citation_doi'}):
                doi = meta['content']
                print '-[ %s ]-' % (doi)
                record_add_field(record,'024','7',' ','',[('a', doi), ('2','DOI'), ('9', 'SISSA')])
                doi1 = re.sub('[\(\)\/]', '_', doi)
            for meta in metapage.find_all('meta', attrs = {'name' : 'citation_abstract'}):
                print '-[abstract]-'
                abstract = meta['content']
                record_add_field(record, '520', ' ', ' ', '', [('a', abstract), ('9', 'SISSA')])
            if not doi:
                record_add_field(record,'024','7',' ','',[('a',nodoi),('2','NODOI')])
            #check for collaborations in author field
            if '700' in record.keys():
                for author in record_delete_fields(record,'700'):
                    na = []
                    for entry in author[0]:
                        if entry[0] == 'a':
                            if re.search('Collaboration', entry[1], re.IGNORECASE):                                
                                newcolls = []
                                (coll, author) = coll_cleanforthe(entry[1])
                                print entry[1], '|', coll, author
                                for scoll in coll_split(coll):
                                    newcolls.append(re.sub('^the ', '', coll_clean710(scoll), re.IGNORECASE))
                                for col in newcolls:
                                    record_add_field(record, '710', ' ', ' ', '', [('g', re.sub(',', '', col))])
                                    print 'found collection "%s" in author field' % (col)
                                if author:
                                    na.append(('a', author))
                            else:
                                na.append(entry)    
                        else:
                            na.append(entry)    
                    if author:
                        record_add_field(record, '700', ' ', ' ', '', na)
            #bibclassify abstract 
            if not abstract:
                tmpfile = tmpdir+'fs'+doi1
                abspdf = '%s%s.abstract.pdf' % (pdftmpdir, doi1)
                os.system('pdftk %s.pdf cat 1 output %s' % (posfile, abspdf))
                if not (os.path.isfile(tmpfile+'.abs.bib')) or (int(os.path.getsize(tmpfile+'.abs.bib'))==0):
                    os.system(bibclassifycommand+abspdf+' > '+tmpfile+'.abs.bib')
                    if not (os.path.isfile(tmpfile+'.abs.antibib')) or (int(os.path.getsize(tmpfile+'.abs.antibib'))==0):
                        os.system(antibibclassifycommand+abspdf+' > '+tmpfile+'.abs.antibib')
            #count pages
            anzahlseiten = os.popen('pdftk %s.pdf dump_data output | grep -i NumberO' % (posfile)).read().strip()
            anzahlseiten = re.sub('.*NumberOfPages. (\d*).*',r'\1',anzahlseiten)
            record_add_field(record, '300', ' ', ' ', '', [('a', anzahlseiten)])
            #remove link since PoS now has DOIs
            record_delete_fields(record, '856')
            if anzahlseiten != '1':
                records.append(record)
                bigxmlfile.write(record_xml_output(record))
            bigxmlfile.write('\n')
    restxmlfile.write('</collection>\n')
    restxmlfile.close()
    bigxmlfile.write('</collection>\n')
    bigxmlfile.close()

    if publicationyearchanged:
        print 'change 773__y to %i' % (publicationyear)
        bigxmlfile = codecs.EncodedFile(codecs.open(xmlpath+'pos_'+cat+'.xml',mode='wb'),'utf8')
        bigxmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n')
        for record in records:
            m773 = record_delete_field(record,'773',' ',' ')
            new773 = []
            for entry in m773[0][0]:
                if entry[0] == 'y':
                    new773.append(('y', str(publicationyear)))
                else:
                    new773.append(entry)
            record_add_field(record, '773', ' ', ' ', '', new773)
            bigxmlfile.write(record_xml_output(record))
            bigxmlfile.write('\n')
        bigxmlfile.write('</collection>\n')
        bigxmlfile.close()
       
    #os.system("cp %spos_%s.xml %s" % (xmlpath,conf_acronym,publisherpath))
    os.system("cp %spos_%s.xml %s" % (xmlpath, cat, publisherpath))
    
    if appendrecs:
        message = '%s %i records with append only\n' % (message,len(appendrecs))
    return message
    
def main(argv):
    """main function"""
    conf = ''
    cnum = ''

    try:
        opts, args = getopt.getopt(argv,"hc:i:",["cnum=","conf="])
    except getopt.GetoptError:
        print 'Usage: pos.py -c <cnum> -i <conf>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: pos.py -c <cnum> -i <conf>'
            sys.exit()
        elif opt in ("-c", "--cnum"):
            cnum = arg
        elif opt in ("-i", "--conf"):
            conf = arg

    if conf == '' or cnum == '':
        print 'Usage: pos.py -c <cnum> -i <conf>'
        sys.exit(2)

    
    message = pos_harvesting(conf,cnum)
    print message
    print 'Starting retinspire'
    #os.system("/afs/desy.de/user/l/library/proc/start_retinspire.pl %spos_%s.xml" % (xmlpath, re.sub(' ', '_', conf)))
    retfiles_text = open(retfiles_path,"r").read()
    line = "pos_%s.xml\n" % (re.sub(' ', '_', conf))
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
    os.system("rm -f %s/*" % (pdftmpdir))

if __name__ == "__main__":
    main(sys.argv[1:])
