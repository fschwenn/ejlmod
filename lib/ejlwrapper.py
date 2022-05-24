#!/usr/bin/python
# this program (called regularly each month) calls dedicated
# programs to harvest journals by scaning homepages
#
# FS: 2012-06-18
#

import datetime
import os
import re
import sys

protocol = "/afs/desy.de/group/library/publisherdata/log/protocol"
#get previous month
if len(sys.argv) == 4:
    today = datetime.date(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
else:
    today = datetime.datetime.now()
if today.month == 1:
    prmonth = 12
    pryear = today.year - 1
else:
    prmonth = today.month - 1 
    pryear = today.year
prquarter = prmonth / 3
prsixth = prmonth / 2
prthird = prmonth / 4
mnrasbignumber = 36*pryear + 3*prmonth - 70759

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

logfile = '/afs/desy.de/group/library/publisherdata/log/ejlwrapper.log.%i.%02d.%02d' % (pryear,prmonth,today.day)
#logfile = '/afs/desy.de/group/library/publisherdata/log/ejlwrapper.log.%i.%i.%i' % (pryear,prmonth,10)
lproc = '/afs/desy.de/user/l/library/proc'
pythoncommand = '/home/library/.virtualenvs/inspire/bin/python'
#journal -> (months between two issues, call)
#        ('physri'      , 1,'%s %s/hindawi.xml.py physri %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('ijmms'      , 1,'%s %s/hindawi.xml.py ijmms %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('gravity'   , 1,'%s %s/hindawi.xml.py gravity  %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('gravity'   , 1,'%s %s/hindawi.xml.py jgrav  %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('aa'        , 6,'%s %s/hindawi.xml.py aa   %i %i'  % (pythoncommand, lproc,pryear,prmonth)),#F
#        ('aaa'        , 6,'%s %s/hindawi.xml.py aaa   %i %i'  % (pythoncommand, lproc,pryear,prmonth)),#F
#        ('isrnhep'   , 1,'%s %s/hindawi.xml.py isrnhep   %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('isrnmp'    , 1,'%s %s/hindawi.xml.py isrnmp   %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('isrnastro' , 1,'%s %s/hindawi.xml.py isrnastro %i %i'  % (pythoncommand, lproc,pryear,prmonth)),
#        ('lrr'       , 1,'%s %s/livingreviews.py %i %i' % (pythoncommand, lproc,pryear,prmonth)),
        #('theses-bicocca', 2, '%s %s/theses-bicocca.py' % (pythoncommand, lproc)),
#        ('jdg'       , 4,'%s %s/intlpress.py jdg %i 1-3'  % (pythoncommand, lproc,(pryear-1983)*3+2+prthird)),
#        ('ajm'       , 3,'%s %s/intlpress.py ajm %i %i'  % (pythoncommand, lproc,pryear-1996,prquarter)),
#        ('cag'       , 2,'%s %s/intlpress.py cag %i %i'  % (pythoncommand, lproc,pryear-1992, prsixth)),
#        ('actaastron', 3, '%s %s/copernicusfoundation.py %i %i' % (pythoncommand, lproc, pryear - 1950, prquarter)),
#        ('plreex'    , 3, '%s %s/iop-crawler.py https://iopscience.iop.org/issue/2516-1067/%i/%i' %  (pythoncommand, lproc, pryear-2018, prquarter)),
#stopped harvesting 2020.06.09 because hardly cited        ('physessays' , 3, '%s %s/ingenta.py pe %i %i %i' % (pythoncommand, lproc, pryear, pryear - 1987, prquarter)),
#        ('theses-reno', 2, '%s %s/theses-reno.py' % (pythoncommand, lproc)), nur master und bachelor
#        ('amsa'      , 2, '%s %s/intlpress.py amsa %i %i'  % (pythoncommand, lproc, pryear-2015, prsixth)),
 #       ('fourier'      , 2, '%s %s/fourier.py %i %i'  % (pythoncommand, lproc, pryear-1950, prsixth)),,
#        ('qjmath'    , 3,'%s %s/oxfordjournals.xml.py qjmath %s %s' % (pythoncommand, lproc, pryear-1949, prquarter)), -> per hand
#        ('ahep'      , 6,'%s %s/hindawi.xml.py ahep %i %i'  % (pythoncommand, lproc,pryear,prmonth)),#F
#        ('amp'       , 6,'%s %s/hindawi.xml.py amp  %i %i'  % (pythoncommand, lproc,pryear,prmonth)),#F
#        ('jam'        , 6,'%s %s/hindawi.xml.py jam   %i %i'  % (pythoncommand, lproc,pryear,prmonth)),#F
#        ('euclid'    , 1,'%s %s/projecteuclid.py' % (pythoncommand, lproc)),#F
#        ('acmp'       , 6,'%s %s/hindawi.xml.py acmp  %i %i'  % (pythoncommand, lproc,pryear,prmonth)),

#TO BE REMOCED: OSA

jnls = [('cjp'       , 1,'%s %s/cjp.py cjp %i %i' % (pythoncommand, lproc,pryear-1922,prmonth)),
        ('theses-oatd I', 2, '%s %s/theses-oatd.py 1 3' % (pythoncommand, lproc)),
        ('rsi'       , 1,'%s %s/aip.xml2.py rsi %i %i' % (pythoncommand, lproc,pryear-1929,prmonth)),
        ('theses-oatd II', 3, '%s %s/theses-oatd.py 3 5' % (pythoncommand, lproc)),
        ('jmp'       , 1,'%s %s/aip.xml2.py jmp %i %i' % (pythoncommand, lproc,pryear-1959,prmonth)),
        ('theses-oatd III', 2, '%s %s/theses-oatd.py 5 7' % (pythoncommand, lproc)),
        ('chaos'     , 3,'%s %s/aip.xml2.py  chaos %i %i' % (pythoncommand, lproc,pryear-1990,prquarter)),
        ('theses-oatd IV', 3, '%s %s/theses-oatd.py 7 9' % (pythoncommand, lproc)),
        ('symmetry'  , 1,'%s %s/mdpi.sftp.py symmetry' % (pythoncommand, lproc)),
        ('sensors'  , 1,'%s %s/mdpi.sftp.py sensors' % (pythoncommand, lproc)),
        ('nanomaterials'  , 1,'%s %s/mdpi.sftp.py nanomaterials' % (pythoncommand, lproc)),
        ('theses-oatd V', 2, '%s %s/theses-oatd.py 9 11' % (pythoncommand, lproc)),
        ('arnps'     ,12,'%s %s/annualreview.py arnps %i' %  (pythoncommand, lproc,pryear-1950)),
        ('theses-oatd VI', 3, '%s %s/theses-oatd.py 11 13' % (pythoncommand, lproc)),
        ('araa'      ,12,'%s %s/annualreview.py araa  %i' %  (pythoncommand, lproc,pryear-1962)),
        ('theses-oatd VII', 2, '%s %s/theses-oatd.py 13 15' % (pythoncommand, lproc)),
        ('prs'       , 1,'%s %s/royalsociety.xml2.py prs %i %i' % (pythoncommand, lproc,pryear-1544,(pryear-1834)*12+prmonth)),
        ('theses-oatd VIII', 3, '%s %s/theses-oatd.py 15 17' % (pythoncommand, lproc)),
        ('actapol'   , 1,'%s %s/actapolytechnica.py' % (pythoncommand, lproc)),
        ('theses-oatd IX', 2, '%s %s/theses-oatd.py 17 19 ' % (pythoncommand, lproc)),
        ('pasj'      , 2,'%s %s/oxfordjournals.xml.py pasj %s %s' % (pythoncommand, lproc, pryear-1948, prsixth)),
        ('theses-oatd X', 3, '%s %s/theses-oatd.py 19 21' % (pythoncommand, lproc)),
        ('ptep'      , 1,'%s %s/oxfordjournals.xml.py ptep %i %i' % (pythoncommand, lproc,pryear,prmonth)),
        ('theses-oatd XI', 2, '%s %s/theses-oatd.py 21 23' % (pythoncommand, lproc)),
        ('kilthub' , 1, '%s %s/figshare.py kilthub' % (pythoncommand, lproc)),
        ('theses-oatd XII', 3, '%s %s/theses-oatd.py 23 25' % (pythoncommand, lproc)),
        ('universe'  , 1,'%s %s/mdpi.sftp.py universe' % (pythoncommand, lproc)),
        ('theses-oatd XIII', 2, '%s %s/theses-oatd.py 25 27' % (pythoncommand, lproc)),
        ('imrn'      , 1,'%s %s/oxfordjournals.xml.py imrn %i %i' % (pythoncommand, lproc,pryear,2*prmonth)),
        ('theses-oatd XIV', 3, '%s %s/theses-oatd.py 27 29 ' % (pythoncommand, lproc)),
        ('apr'       , 3,'%s %s/ccsenet.py apr %i %i'  % (pythoncommand, lproc,pryear-2008,prquarter)),
        ('theses-oatd XV', 2, '%s %s/theses-oatd.py 29 31' % (pythoncommand, lproc)),
        ('jmr'       , 2,'%s %s/ccsenet.py jmr %i %i'  % (pythoncommand, lproc,pryear-2008,prsixth)),
        ('cms'       , 3,'%s %s/intlpress.py cms %i %i'  % (pythoncommand, lproc,pryear-2002,prquarter)),
        ('mnras', 1, '%s %s/oxfordjournals.xml.py mnras %s %s' % (pythoncommand, lproc, mnrasbignumber/4, mnrasbignumber % 4 + 1)),
        ('mnras', 1, '%s %s/oxfordjournals.xml.py mnras %s %s' % (pythoncommand, lproc, (mnrasbignumber+1)/4, (mnrasbignumber+1)%4 + 1)),
        ('mnras', 1, '%s %s/oxfordjournals.xml.py mnras %s %s' % (pythoncommand, lproc, (mnrasbignumber+2)/4, (mnrasbignumber+2)%4 + 1)),
        ('theses-boston', 2, '%s %s/theses-boston.py' % (pythoncommand, lproc)),
        ('aanda'     , 1,'%s %s/edpjournals.py aanda %i %02i' % (pythoncommand, lproc,pryear,prmonth)),
        ('jsg'       , 3,'%s %s/intlpress.py jsg %i %s'  % (pythoncommand, lproc,pryear-2002, prquarter)),
        ('ltp'       , 1,'%s %s/aip.xml2.py ltp %i %i' % (pythoncommand, lproc,pryear-1974,prmonth)),
        ('mnrasl', 1, '%s %s/oxfordjournals.xml.py mnrasl %s 1' % (pythoncommand, lproc, mnrasbignumber/4)),
        ('sps'       , 2,'%s %s/scipost.py sps %i %i' % (pythoncommand, lproc, 2*(pryear-2016) + prmonth/6, prmonth % 6 + 1)),
        ('bjps'      , 3,'%s %s/oxfordjournals.xml.py bjps %i %i' % (pythoncommand, lproc,pryear-1949,prquarter)),
        ('imrn'      , 1,'%s %s/oxfordjournals.xml.py imrn %i %i' % (pythoncommand, lproc,pryear,2*prmonth-1)),
        ('monash', 1,'%s %s/figshare.py monash' % (pythoncommand, lproc)),
        ('galaxies'  , 1,'%s %s/mdpi.sftp.py galaxies' % (pythoncommand, lproc)),
        ('entropy'   , 1,'%s %s/mdpi.sftp.py entropy' % (pythoncommand, lproc)),
        ('cambridgebooks', 1, '%s %s/cambridgebooks.xml.py' % (pythoncommand, lproc)),
        ('oxfordbooks', 1, '%s %s/oxfordbooks.py' % (pythoncommand, lproc)),
        ('wspbooks', 1, '%s %s/wspbooks.py' % (pythoncommand, lproc)),
        ('theses-kit', 2, '%s %s/theses-kit.py' % (pythoncommand, lproc)),
        ('theses-ora', 3, '%s %s/theses-ora.py' % (pythoncommand, lproc)),
        ('theses-nikhef', 2, '%s %s/theses-nikhef.py' % (pythoncommand, lproc)),
        ('theses-clas', 2, '%s %s/theses-clas.py' % (pythoncommand, lproc)),
        ('theses-kentucky', 2, '%s %s/theses-kentucky.py' % (pythoncommand, lproc)),
        ('theses-sissa', 2, '%s %s/theses-sissa.py' % (pythoncommand, lproc)),
        ('theses-maryland', 2, '%s %s/theses-maryland.py' % (pythoncommand, lproc)),
        ('ryerson' , 1, '%s %s/figshare.py ryerson' % (pythoncommand, lproc)),
        ('theses-belle', 2, '%s %s/theses-belle.py' % (pythoncommand, lproc)),
        ('theses-CSUC', 2, '%s %s/theses-CSUC.py' % (pythoncommand, lproc)),
        ('theses-cambridge', 2, '%s %s/theses-cambridge.py' % (pythoncommand, lproc)),
        ('theses-pennstate', 2, '%s %s/theses-pennstate.py' % (pythoncommand, lproc)),
        ('theses-DCN', 2, '%s %s/theses-DCN.py' % (pythoncommand, lproc)),
        ('theses-PANDA', 2, '%s %s/theses-PANDA.py' % (pythoncommand, lproc)),
        ('php'       , 1,'%s %s/aip.xml2.py php %i %i' % (pythoncommand, lproc,pryear-1993,prmonth)),
        ('OSAol', 1, '%s  %s/osa.py ol %i %i'  % (pythoncommand, lproc,pryear-1975, prmonth * 2 - 1)),
        ('OSAol', 1, '%s  %s/osa.py ol %i %i'  % (pythoncommand, lproc,pryear-1975, prmonth * 2)),
        ('OSAoe', 1, '%s  %s/osa.py oe %i %i'  % (pythoncommand, lproc,pryear-1992, prmonth * 2 - 1)),
        ('OSAoe', 1, '%s  %s/osa.py oe %i %i'  % (pythoncommand, lproc,pryear-1992, prmonth * 2)),
        ('OSAao', 1, '%s  %s/osa.py ao %i %i'  % (pythoncommand, lproc,pryear-1961, prmonth * 3 - 2)),
        ('OSAao', 1, '%s  %s/osa.py ao %i %i'  % (pythoncommand, lproc,pryear-1961, prmonth * 3 - 1)),
        ('OSAao', 1, '%s  %s/osa.py ao %i %i'  % (pythoncommand, lproc,pryear-1961, prmonth * 3)),
        ('OSAjosaa', 1, '%s  %s/osa.py josaa %i %i'  % (pythoncommand, lproc,pryear-1983, prmonth)),
        ('OSAjosab', 1, '%s  %s/osa.py josab %i %i'  % (pythoncommand, lproc,pryear-1983, prmonth)),
        ('adva', 1, '%s %s/aip.xml2.py adva %i %i' % (pythoncommand, lproc,pryear-2010,prmonth)),
        ('particles', 1, '%s %s/mdpi.sftp.py particles' % (pythoncommand, lproc)),
        ('physics', 1, '%s %s/mdpi.sftp.py physics' % (pythoncommand, lproc)),
        ('mnras', 1, '%s %s/oxfordjournals.xml.py mnras %s %s in_progress' % (pythoncommand, lproc, 1 + mnrasbignumber/4, mnrasbignumber % 4 + 1)),
        ('mnras', 1, '%s %s/oxfordjournals.xml.py mnras %s %s in_progress' % (pythoncommand, lproc, 1 + (mnrasbignumber+1)/4, (mnrasbignumber+1)%4 + 1)),
        ('mnras', 1, '%s %s/oxfordjournals.xml.py mnras %s %s in_progress' % (pythoncommand, lproc, 1 + (mnrasbignumber+2)/4, (mnrasbignumber+2)%4 + 1)),
        ('mnrasl', 1, '%s %s/oxfordjournals.xml.py mnrasl %s 1 in_progress' % (pythoncommand, lproc, 1 + mnrasbignumber/4)),
        ('apl'       , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924 + ((prmonth-1) / 6), 1 + (4*prmonth - 3) % 24)),
        ('apl'       , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924 + ((prmonth-1) / 6), 1 + (4*prmonth - 2) % 24)),
        ('apl'       , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924 + ((prmonth-1) / 6), 1 + (4*prmonth - 1) % 24)),
        ('apl'       , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924 + ((prmonth-1) / 6), 1 + 4*prmonth % 24)),
        ('jcp'       , 1, '%s %s/aip.xml2.py jcp %i %i' % (pythoncommand, lproc, 2*pryear - 3888 + ((prmonth-1) / 6), 1 + (4*prmonth - 3) % 24)),
        ('jcp'       , 1, '%s %s/aip.xml2.py jcp %i %i' % (pythoncommand, lproc, 2*pryear - 3888 + ((prmonth-1) / 6), 1 + (4*prmonth - 2) % 24)),
        ('jcp'       , 1, '%s %s/aip.xml2.py jcp %i %i' % (pythoncommand, lproc, 2*pryear - 3888 + ((prmonth-1) / 6), 1 + (4*prmonth - 1) % 24)),
        ('jcp'       , 1, '%s %s/aip.xml2.py jcp %i %i' % (pythoncommand, lproc, 2*pryear - 3888 + ((prmonth-1) / 6), 1 + 4*prmonth % 24)),
        ('jap'       , 1, '%s %s/aip.xml2.py jap %i %i' % (pythoncommand, lproc, 2*pryear - 3913 + ((prmonth-1) / 6), 1 + (4*prmonth - 3) % 24)),
        ('jap'       , 1, '%s %s/aip.xml2.py jap %i %i' % (pythoncommand, lproc, 2*pryear - 3913 + ((prmonth-1) / 6), 1 + (4*prmonth - 2) % 24)),
        ('jap'       , 1, '%s %s/aip.xml2.py jap %i %i' % (pythoncommand, lproc, 2*pryear - 3913 + ((prmonth-1) / 6), 1 + (4*prmonth - 1) % 24)),
        ('jap'       , 1, '%s %s/aip.xml2.py jap %i %i' % (pythoncommand, lproc, 2*pryear - 3913 + ((prmonth-1) / 6), 1 + 4*prmonth % 24)),
        ('procnas'   , 1, '%s %s/procnas.py %i %i,%i' % (pythoncommand, lproc, pryear-1903, 4*(prmonth-1)+1, 4*(prmonth-1)+2)),
        ('procnas'   , 1, '%s %s/procnas.py %i %i,%i' % (pythoncommand, lproc, pryear-1903, 4*(prmonth-1)+3, 4*(prmonth-1)+4)),
        ('arcmp'     ,12, '%s %s/annualreview.py arcmp  %i' %  (pythoncommand, lproc,pryear-2009)),
        ('theses-kit_etp', 2, '%s %s/theses-kit_etp.py' % (pythoncommand, lproc)),
        ('condensedmatter'   , 1,'%s %s/mdpi.sftp.py condensedmatter' % (pythoncommand, lproc)),
        ('atoms'   , 1,'%s %s/mdpi.sftp.py atoms' % (pythoncommand, lproc)),
        ('ajp'       , 1,'%s %s/aip.xml2.py ajp %i %i' % (pythoncommand, lproc,pryear-1932,prmonth)),
        ('jatis'     , 3, '%s %s/spie_journal.py jatis %i %i' % (pythoncommand, lproc, pryear-2014, prquarter)),
        ('messenger' , 3, '%s %s/messenger.py %i' % (pythoncommand, lproc, 4*pryear + prquarter - 7902)),
        ('phf'       , 1, '%s %s/aip.xml2.py phf %i %i' % (pythoncommand, lproc, pryear - 1988, prmonth)),
        ('science', 1, '%s %s/sciencemag.py science %i' % (pythoncommand, lproc, pryear)),
        ('scienceadvances', 1, '%s %s/sciencemag.py sciadv %i' % (pythoncommand, lproc, pryear)),
        ('theses-unesp', 2, '%s %s/theses-unesp.py' % (pythoncommand, lproc)),
        ('theses-eth', 2, '%s %s/theses-eth.py' % (pythoncommand, lproc)),
        ('theses-goettingen', 2, '%s %s/theses-goettingen.py' % (pythoncommand, lproc)),
        ('theses-hub', 2, '%s %s/theses-hub.py' % (pythoncommand, lproc)),
        ('theses-mit', 2, '%s %s/theses-mit.py' % (pythoncommand, lproc)),
        ('theses-unibo', 1, '%s %s/theses-unibo.py' % (pythoncommand, lproc)),
        ('theses-heidelberg', 1, '%s %s/theses-heidelberg.py' % (pythoncommand, lproc)),
        ('theses-rutgers', 1, '%s %s/theses-rutgers.py' % (pythoncommand, lproc)),
        ('theses-frankfurt', 2, '%s %s/theses-frankfurt.py' % (pythoncommand, lproc)),
        ('theses-diva', 1, '%s %s/theses-diva.py' % (pythoncommand, lproc)),
        ('theses-tum', 1, '%s %s/theses-tum.py' % (pythoncommand, lproc)),
        ('theses-waterloo', 2, '%s %s/theses-waterloo.py' % (pythoncommand, lproc)),
        ('theses-princeton', 2, '%s %s/theses-princeton.py' % (pythoncommand, lproc)),
        ('theses-capetown', 2, '%s %s/theses-capetown.py' % (pythoncommand, lproc)),
        ('science', 1, '%s %s/sciencemag.py science %i' % (pythoncommand, lproc, pryear)),
        ('scienceadvances', 1, '%s %s/sciencemag.py sciadv %i' % (pythoncommand, lproc, pryear)),
        ('theses-uam', 1, '%s %s/theses-uam.py' % (pythoncommand, lproc)),
        ('theses-durham', 2, '%s %s/theses-durham.py' % (pythoncommand, lproc)),
        ('theses-southampton', 2, '%s %s/theses-southampton.py' % (pythoncommand, lproc)),
        ('theses-imperial', 2, '%s %s/theses-imperial.py' % (pythoncommand, lproc)),
        ('theses-bern', 2, '%s %s/theses-bern.py' % (pythoncommand, lproc)),
        ('theses-edinburgh', 2, '%s %s/theses-edinburgh.py' % (pythoncommand, lproc)),
        ('theses-kyoto', 2, '%s %s/theses-kyoto.py' % (pythoncommand, lproc)),
        ('theses-narcis', 1, '%s %s/theses-narcis.py' % (pythoncommand, lproc)),
        ('theses-tud', 2, '%s %s/theses-tud.py' % (pythoncommand, lproc)),
        ('theses-surreyISSUE', 1, '%s %s/theses-surrey.py' % (pythoncommand, lproc)),
        ('theses-lmu', 2, '%s %s/theses-lmu.py' % (pythoncommand, lproc)),
        ('theses-regensburg', 1, '%s %s/theses-regensburg.py' % (pythoncommand, lproc)),
        ('theses-helsinki', 2, '%s %s/theses-helda.py' % (pythoncommand, lproc)),
        ('theses-saopaulo', 2, '%s %s/theses-saopaulo.py' % (pythoncommand, lproc)),
        ('theses-wm', 2, '%s %s/theses-wm.py' % (pythoncommand, lproc)),
        ('theses-michigan', 2, '%s %s/theses-michigan.py' % (pythoncommand, lproc)),
        ('theses-epfl', 2, '%s %s/theses-epfl.py' % (pythoncommand, lproc)),
        ('theses-erlangen', 2, '%s %s/theses-erlangen.py' % (pythoncommand, lproc)),
        ('theses-ucla_ucla', 1, '%s %s/theses-ucla.py ucla' % (pythoncommand, lproc)),
        ('theses-wurzburg', 1, '%s %s/theses-wuerzburg.py' % (pythoncommand, lproc)),
        ('theses-oklahoma', 1, '%s %s/theses-oklahoma.py' % (pythoncommand, lproc)),
        ('theses-infn???', 1, '%s %s/theses-infn.py' % (pythoncommand, lproc)),
        ('theses-ino', 2, '%s %s/theses-ino.py' % (pythoncommand, lproc)),
        ('theses-cologne', 2, '%s %s/theses-cologne.py' % (pythoncommand, lproc)),
        ('theses-ctu', 2, '%s %s/theses-charles.py' % (pythoncommand, lproc)),
        ('theses-victoria', 2, '%s %s/theses-victoria.py' % (pythoncommand, lproc)),
        ('theses-valencia', 2, '%s %s/theses-valencia.py' % (pythoncommand, lproc)),
        ('theses-bielefeld', 2, '%s %s/theses-bielefeld.py' % (pythoncommand, lproc)),
        ('theses-cracow', 2, '%s %s/theses-cracow.py' % (pythoncommand, lproc)),
        ('theses-cornell', 2, '%s %s/theses-cornell.py' % (pythoncommand, lproc)),
        ('theses-texasam', 2, '%s %s/theses-texasam.py' % (pythoncommand, lproc)),
        ('theses-gent', 2, '%s %s/theses-gent.py' % (pythoncommand, lproc)),
        ('theses-mainz', 2, '%s %s/theses-mainz.py' % (pythoncommand, lproc)),
        ('theses-texas', 2, '%s %s/theses-texas.py' % (pythoncommand, lproc)),
        ('theses-johnhopkins', 2, '%s %s/theses-johnhopkins.py' % (pythoncommand, lproc)),
        ('theses-sidney', 2, '%s %s/theses-sidney.py' % (pythoncommand, lproc)),
        ('theses-toronto', 2, '%s %s/theses-toronto.py' % (pythoncommand, lproc)),
        ('theses-arizona', 2, '%s %s/theses-arizona.py' % (pythoncommand, lproc)),
        ('theses-carleton', 2, '%s %s/theses-carleton.py' % (pythoncommand, lproc)),
        ('theses-duke', 2, '%s %s/theses-duke.py' % (pythoncommand, lproc)),
        ('theses-ucla_ucd', 1, '%s %s/theses-ucla.py ucd' % (pythoncommand, lproc)),
        ('theses-ucla_uci', 1, '%s %s/theses-ucla.py uci' % (pythoncommand, lproc)),
        ('theses-ucla_ucb', 1, '%s %s/theses-ucla.py ucb' % (pythoncommand, lproc)),
        ('theses-ucla_ucr', 1, '%s %s/theses-ucla.py ucr' % (pythoncommand, lproc)),
        ('theses-ucla_ucsd', 1, '%s %s/theses-ucla.py ucsd' % (pythoncommand, lproc)),
        ('theses-ucla_ucsf', 1, '%s %s/theses-ucla.py ucsf' % (pythoncommand, lproc)),
        ('theses-ucla_ucsb', 1, '%s %s/theses-ucla.py ucsb' % (pythoncommand, lproc)),
        ('theses-ucla_ucsc', 1, '%s %s/theses-ucla.py ucsc' % (pythoncommand, lproc)),
        ('theses-shodhganga_Astro', 3, '%s %s/theses-shodganga.py Astro 1 500' % (pythoncommand, lproc)),
        ('theses-shodhganga_Physic1', 2, '%s %s/theses-shodganga.py Physics 1 50' % (pythoncommand, lproc)),
        ('theses-shodhganga_Physic2', 2, '%s %s/theses-shodganga.py Physics 51 100' % (pythoncommand, lproc)),
        ('theses-shodhganga_Physic3', 2, '%s %s/theses-shodganga.py Physics 101 150' % (pythoncommand, lproc)),
        ('theses-shodhganga_Physic4', 2, '%s %s/theses-shodganga.py Physics 151 200' % (pythoncommand, lproc)),
        ('theses-shodhganga_Physic5', 2, '%s %s/theses-shodganga.py Physics 201 500' % (pythoncommand, lproc)),
        ('theses-aachen', 2, '%s %s/theses-aachen.py' % (pythoncommand, lproc)),
        ('theses-harvard', 2, '%s %s/theses-harvard.py' % (pythoncommand, lproc)),
        ('theses-shodhganga_Math1', 3, '%s %s/theses-shodganga.py Math 1 50' % (pythoncommand, lproc)),
        ('theses-shodhganga_Math2', 3, '%s %s/theses-shodganga.py Math 51 100' % (pythoncommand, lproc)),
        ('theses-shodhganga_Math3', 3, '%s %s/theses-shodganga.py Math 101 150' % (pythoncommand, lproc)),
        ('theses-shodhganga_Math4', 3, '%s %s/theses-shodganga.py Math 151 200' % (pythoncommand, lproc)),
        ('theses-shodhganga_Math5', 3, '%s %s/theses-shodganga.py Math 201 500' % (pythoncommand, lproc)),
        ('joss', 1,'%s %s/theoj.py joss' % (pythoncommand, lproc)),
        ('theses-ibict_physics', 2, '%s %s/theses-ibict.py physics' % (pythoncommand, lproc)),
        ('theses-ibict_math', 2, '%s %s/theses-ibict.py math' % (pythoncommand, lproc)),
        ('theses-ibict_nucl', 2, '%s %s/theses-ibict.py nucl' % (pythoncommand, lproc)),
        ('theses-ibict_physpost', 2, '%s %s/theses-ibict.py physpost' % (pythoncommand, lproc)),
        ('theses-prr', 2, '%s %s/theses-prr.py' % (pythoncommand, lproc)),
        ('theses-freiburg', 2, '%s %s/theses-freiburg.py' % (pythoncommand, lproc)),
        ('theses-montreal', 2, '%s %s/theses-montreal.py' % (pythoncommand, lproc)),
        ('theses-hamburg', 2, '%s %s/theses-hamburg.py' % (pythoncommand, lproc)),
        ('theses-nielsbohr', 3, '%s %s/theses-nielsbohr.py' % (pythoncommand, lproc)),
        ('theses-pittsburgh', 2, '%s %s/theses-pittsburgh.py' % (pythoncommand, lproc)),
        ('theses-unlp', 3, '%s %s/theses-unlp.py' % (pythoncommand, lproc)),
        ('theses-simonfraser', 3, '%s %s/theses-simonfraser.py' % (pythoncommand, lproc)),
        ('theses-liverpool', 2, '%s %s/theses-liverpool.py' % (pythoncommand, lproc)),
        ('theses-baylor', 2, '%s %s/theses-baylor.py' % (pythoncommand, lproc)),
        ('theses-mcgill', 2, '%s %s/theses-mcgill.py' % (pythoncommand, lproc)),
        ('theses-uclondon', 2, '%s %s/theses-uclondon.py' % (pythoncommand, lproc)),
        ('theses-milanbicocca', 2, '%s %s/theses-italy.py milanbicocca' % (pythoncommand, lproc)),
        ('theses-adelaide', 3, '%s %s/theses-adelaide.py' % (pythoncommand, lproc)),
        ('theses-glasgow', 2, '%s %s/theses-glasgow.py' % (pythoncommand, lproc)),
        ('theses-siegen', 2, '%s %s/theses-siegen.py' % (pythoncommand, lproc)),
        ('theses-basel', 2, '%s %s/theses-basel.py' % (pythoncommand, lproc)),
        ('theses-britishcolumbia', 2, '%s %s/theses-britishcolumbia.py' % (pythoncommand, lproc)),
        ('theses-bonn', 2, '%s %s/theses-bonn2.py %i' % (pythoncommand, lproc, pryear)),
        ('theses-granada', 2, '%s %s/theses-granada.py' % (pythoncommand, lproc)),
        ('theses-stanford', 2, '%s %s/theses-stanford.py' % (pythoncommand, lproc)),
        ('theses-chilecatolica', 3, '%s %s/theses-chilecatolica.py' % (pythoncommand, lproc)),
        ('theses-wuppertal', 3, '%s %s/theses-wuppertal.py' % (pythoncommand, lproc)),
        ('theses-kansas', 3, '%s %s/theses-kansas.py' % (pythoncommand, lproc)),
        ('theses-chicago', 2, '%s %s/theses-chicago.py' % (pythoncommand, lproc)),
        ('theses-padua', 2, '%s %s/theses-padua.py' % (pythoncommand, lproc)),
        ('theses-purdue', 2, '%s %s/theses-purdue.py' % (pythoncommand, lproc)),
        ('theses-columbia', 1, '%s %s/theses-columbia.py' % (pythoncommand, lproc)),
        ('theses-tel', 1, '%s %s/theses-tel.py' % (pythoncommand, lproc)),
        ('theses-sussex', 2, '%s %s/theses-sussex.py' % (pythoncommand, lproc)),
        ('theses-federicosantamaria', 2, '%s %s/theses-federicosantamaria.py' % (pythoncommand, lproc)),
        ('theses-hannover', 2, '%s %s/theses-hannover.py' % (pythoncommand, lproc)),
        ('theses-leedssheffieldyorkISSUE', 2, '%s %s/theses-leedssheffieldyork.py' % (pythoncommand, lproc)),
        ('theses-stonybrook', 2, '%s %s/theses-stonybrook.py' % (pythoncommand, lproc)),
        ('theses-nust', 2, '%s %s/theses-nust.py' % (pythoncommand, lproc)),
        ('theses-cbpf', 2, '%s %s/theses-cbpf.py' % (pythoncommand, lproc)),
        ('theses-chennai', 2, '%s %s/theses-chennai.py' % (pythoncommand, lproc)),
        ('theses-caltech', 2, '%s %s/theses-caltech.py' % (pythoncommand, lproc)),
        ('theses-iowa', 2, '%s %s/theses-iowa.py' % (pythoncommand, lproc)),
        ('jva', 2, '%s %s/aip.xml2.py jva %i %i' % (pythoncommand, lproc, pryear-1982, prsixth)),
        ('jvb', 2, '%s %s/aip.xml2.py jvb %i %i' % (pythoncommand, lproc, pryear-1982, prsixth)),
        ('mathematics' , 1,'%s %s/mdpi.sftp.py mathematics' % (pythoncommand, lproc)),
        ('theses-floridastate', 2, '%s %s/theses-floridastate.py' % (pythoncommand, lproc)),
        ('theses-southermethodist', 3, '%s %s/theses-southermethodist.py' % (pythoncommand, lproc)),
        ('theses-tubingen', 2, '%s %s/theses-tubingen.py' % (pythoncommand, lproc)),
        ('theses-waynestate', 2, '%s %s/theses-waynestate.py' % (pythoncommand, lproc)),
        ('theses-thueringen', 2, '%s %s/theses-thueringen.py' % (pythoncommand, lproc)),
        ('theses-minnesota', 1, '%s %s/theses-minnesota.py' % (pythoncommand, lproc)),
        ('astrogeo'    , 2,'%s %s/oxfordjournals.xml.py astrogeo %s %s' % (pythoncommand, lproc, pryear-1959, prsixth)),
        ('theses-indiana', 2, '%s %s/theses-indiana.py' % (pythoncommand, lproc)),
        ('theses-alberta', 1, '%s %s/theses-alberta.py' % (pythoncommand, lproc)),
        ('theses-mississippi', 2, '%s %s/theses-mississippi.py' % (pythoncommand, lproc)),
        ('theses-vtech', 3, '%s %s/theses-vtech.py' % (pythoncommand, lproc)),
        ('theses-vcommonwealth', 3, '%s %s/theses-vcommonwealth.py' % (pythoncommand, lproc)),
        ('comaphy' , 3, '%s %s/comaphy.py %i %i' % (pythoncommand, lproc, pryear-1998, prquarter)),
        ('theses-tokyo', 2, '%s %s/theses-tokyo.py' % (pythoncommand, lproc)),
        ('theses-unlp', 2, '%s %s/theses-unlp.py' % (pythoncommand, lproc)),
        ('theses-dresden', 2, '%s %s/theses-dresden.py' % (pythoncommand, lproc)),
        ('theses-northcarolina', 2, '%s %s/theses-northcarolina.py' % (pythoncommand, lproc)),
        ('theses-gsi', 2, '%s %s/theses-gsi.py' % (pythoncommand, lproc)),
        ('theses-osti', 2, '%s %s/theses-osti.py' % (pythoncommand, lproc)),
        ('theses-brown', 3, '%s %s/theses-brown.py' % (pythoncommand, lproc)),
        ('theses-lancaster', 3, '%s %s/theses-lancaster.py' % (pythoncommand, lproc)),
        ('theses-warwick', 3, '%s %s/theses-warwick.py' % (pythoncommand, lproc)),
        ('theses-rome', 2, '%s %s/theses-rome.py' % (pythoncommand, lproc)),
        ('theses-lund', 2, '%s %s/theses-lund.py' % (pythoncommand, lproc)),
        ('theses-trento', 2, '%s %s/theses-italy.py trento' % (pythoncommand, lproc)),
        ('theses-pavia', 2, '%s %s/theses-italy.py pavia' % (pythoncommand, lproc)),
        ('theses-turinpoly', 2, '%s %s/theses-italy.py turinpoly' % (pythoncommand, lproc)),
        ('theses-milan', 2, '%s %s/theses-italy.py milan' % (pythoncommand, lproc)),
        ('theses-udine', 2, '%s %s/theses-italy.py udine' % (pythoncommand, lproc)),
        ('theses-genoa', 2, '%s %s/theses-italy.py genoa' % (pythoncommand, lproc)),
        ('theses-ferrara', 3, '%s %s/theses-italy.py ferrara' % (pythoncommand, lproc)),
        ('theses-siena', 3, '%s %s/theses-italy.py siena' % (pythoncommand, lproc)),
        ('theses-verona', 3, '%s %s/theses-italy.py verona' % (pythoncommand, lproc)),
        ('theses-cagliari', 2, '%s %s/theses-italy.py cagliari' % (pythoncommand, lproc)),
        ('theses-sns', 2, '%s %s/theses-italy.py sns' % (pythoncommand, lproc)),
        ('theses-cagliarieprints' , 2, '%s %s/theses-italy.py cagliarieprints'  % (pythoncommand, lproc)),
        ('theses-oslo', 3, '%s %s/theses-oslo.py' % (pythoncommand, lproc)),
        ('theses-naples', 3, '%s %s/theses-naples.py' % (pythoncommand, lproc)),
        ('theses-cantabria', 3, '%s %s/theses-cantabria.py' % (pythoncommand, lproc)),
        ('theses-coimbra', 3, '%s %s/theses-coimbra.py' % (pythoncommand, lproc)),
        ('theses-salerno', 3, '%s %s/theses-salerno.py' % (pythoncommand, lproc)),
        ('theses-kamiokande', 3, '%s %s/theses-kamiokande.py' % (pythoncommand, lproc)),
        ('theses-louvain', 3, '%s %s/theses-louvain.py' % (pythoncommand, lproc)),
        ('theses-bogota', 6, '%s %s/theses-bogota.py' % (pythoncommand, lproc)),
        ('theses-graz', 2, '%s %s/theses-graz.py' % (pythoncommand, lproc)),
        ('theses-osaka', 2, '%s %s/theses-osaka.py' % (pythoncommand, lproc)),
        ('theses-kingscollege', 3, '%s %s/theses-kingscollege.py' % (pythoncommand, lproc)),
        ('theses-okayama', 3, '%s %s/theses-okayama.py' % (pythoncommand, lproc)),
        ('theses-parma', 2, '%s %s/theses-italy.py parma' % (pythoncommand, lproc)),
        ('theses-washington', 2, '%s %s/theses-washington.py' % (pythoncommand, lproc)),
        ('theses-queenmary', 2, '%s %s/theses-queenmary.py' % (pythoncommand, lproc)),
        ('theses-trinity', 3, '%s %s/theses-trinity.py' % (pythoncommand, lproc)),
        ('theses-jyvaskyla', 3, '%s %s/theses-jyvaskyla.py' % (pythoncommand, lproc)),
        ('theses-ohio', 2, '%s %s/theses-ohio.py' % (pythoncommand, lproc)),
        ('theses-manitoba', 1, '%s %s/theses-manitoba.py' % (pythoncommand, lproc)),
        ('theses-canterbury', 2, '%s %s/theses-canterbury.py' % (pythoncommand, lproc)),
        ('theses-saskatchewan', 2, '%s %s/theses-saskatchewan.py' % (pythoncommand, lproc)),
        ('theses-manchester', 1, '%s %s/theses-manchester.py' % (pythoncommand, lproc)),
        ('theses-compostella', 2, '%s %s/theses-compostella.py' % (pythoncommand, lproc)),
        ('theses-riogrande', 2, '%s %s/theses-riogrande.py' % (pythoncommand, lproc)),
        ('cahiers', 6, '%s %s/cahiers.py' % (pythoncommand, lproc)),
        ('theses-tuwien', 2, '%s %s/theses-tuwien.py' % (pythoncommand, lproc)),
        ('theses-amsterdam', 2, '%s %s/theses-amsterdam.py' % (pythoncommand, lproc)),
        ('theses-colombiaunatl', 3, '%s %s/theses-colombiaunatl.py' % (pythoncommand, lproc)),
        ('theses-northeastern', 1, '%s %s/theses-northeastern.py' % (pythoncommand, lproc)),
        ('theses-forskningsdatabasen', 1, '%s %s/theses-forskningsdatabasen.py' % (pythoncommand, lproc)), #stopped January 2021
        ('theses-arizona_u', 2, '%s %s/theses-arizona_u.py' % (pythoncommand, lproc)),
        ('theses-geneve', 2, '%s %s/theses-geneve.py' % (pythoncommand, lproc)),
        ('theses-hawc', 3, '%s %s/theses-hawc.py' % (pythoncommand, lproc)),
        ('theses-concepcion', 3, '%s %s/theses-concepcion.py' % (pythoncommand, lproc)),
        ('theses-illinois', 2, '%s %s/theses-illinois.py' % (pythoncommand, lproc)),
        ('theses-melbourne', 2, '%s %s/theses-melbourne.py' % (pythoncommand, lproc)),
        ('theses-barcelona', 2, '%s %s/theses-barcelona.py' % (pythoncommand, lproc)),
        ('theses-seoulnatlu', 2, '%s %s/theses-seoulnatlu.py' % (pythoncommand, lproc)),
        ('quantum', 1, '%s %s/quantum.py %i' % (pythoncommand, lproc, pryear-2016)),
        ('OSAoptica', 1, '%s  %s/osa.py optica %i %i'  % (pythoncommand, lproc,pryear-2013, prmonth)),
        ('quantumrep'  , 1,'%s %s/mdpi.sftp.py quantumrep' % (pythoncommand, lproc)),
        ('aqs'     , 3, '%s %s/aip.xml2.py  aqs %i %i' % (pythoncommand, lproc,pryear-2018,prquarter)),
        ('theses-witwatersrand', 3, '%s %s/theses-witwatersrand.py' % (pythoncommand, lproc)),
        ('theses-birmingham', 2, '%s %s/theses-birmingham.py' % (pythoncommand, lproc)),
        ('theses-montana', 2, '%s %s/theses-montana.py' % (pythoncommand, lproc)),
        ('theses-zurich', 2, '%s %s/theses-zurich.py' % (pythoncommand, lproc)),
        ('theses-warsaw', 2, '%s %s/theses-warsaw.py' % (pythoncommand, lproc)),
        ('theses-zagreb', 2, '%s %s/theses-zagreb.py' % (pythoncommand, lproc)),
        ('spsc'       , 3,'%s %s/scipost.py spsc %i %i' % (pythoncommand, lproc, pryear-2017, prquarter)),
        ('spsln'       , 2,'%s %s/scipost.py spsln' % (pythoncommand, lproc)),
        ('lboro' , 1, '%s %s/figshare.py lboro' % (pythoncommand, lproc)),
        ('pto', 1, '%s %s/aip.xml2.py pto %i %i' % (pythoncommand, lproc, pryear-1947, prmonth)),
        ('ljp', 3, '%s %s/ljp.py' % (pythoncommand, lproc)),
        ('nalefd', 1, '%s %s/acs.py nalefd %i %i' % (pythoncommand, lproc, pryear-2000, prmonth)),
        ('jctcce', 1, '%s %s/acs.py jctcce %i %i' % (pythoncommand, lproc, pryear-2004, prmonth)),
        ('apchd5', 1, '%s %s/acs.py apchd5 %i %i' % (pythoncommand, lproc, pryear-2013, prmonth)),
        ('theses-trieste', 2, '%s %s/theses-italy.py trieste' % (pythoncommand, lproc)),
        ('theses-northernillinois', 3, '%s %s/theses-northernillinois.py' % (pythoncommand, lproc)),
        ('theses-leuven', 1, '%s %s/theses-leuven.py' % (pythoncommand, lproc)),
        ('msp', 2, '%s %s/msp.py'  % (pythoncommand, lproc)),
        ('theses-izmir', 3, '%s %s/theses-izmir.py' % (pythoncommand, lproc)),
        ('theses-kansasu', 2, '%s %s/theses-kansasu.py' % (pythoncommand, lproc)),
        ('theses-barcelonaautonoma', 2, '%s %s/theses-barcelonaautonoma.py' % (pythoncommand, lproc)),
        ('theses-mcmaster', 2, '%s %s/theses-mcmaster.py' % (pythoncommand, lproc)),
        ('theses-oregon', 2, '%s %s/theses-oregon.py' % (pythoncommand, lproc)),
        ('theses-brunel', 2, '%s %s/theses-brunel.py' % (pythoncommand, lproc)),
        ('theses-paraiba', 3, '%s %s/theses-paraiba.py' % (pythoncommand, lproc)),
        ('theses-dart', 2, '%s %s/theses-dart.py' % (pythoncommand, lproc)),
        ('theses-didaktorika', 1, '%s %s/theses-didaktorika.py' % (pythoncommand, lproc)),
        ('theses-giessen', 2, '%s %s/theses-giessen.py' % (pythoncommand, lproc)),
        ('theses-bochum', 2, '%s %s/theses-bochum.py' % (pythoncommand, lproc)),
        ('theses-lisbon', 2, '%s %s/theses-lisbon.py' % (pythoncommand, lproc)),
        ('theses-munster', 2, '%s %s/theses-munster.py' % (pythoncommand, lproc)),
        ('theses-houston', 3, '%s %s/theses-houston.py' % (pythoncommand, lproc)),
        ('theses-iisc', 3, '%s %s/theses-iisc.py' % (pythoncommand, lproc)),
        ('applsci'   , 1,'%s %s/mdpi.sftp.py applsci' % (pythoncommand, lproc)),
        ('theses-hawaii', 2, '%s %s/theses-hawaii.py' % (pythoncommand, lproc)),
        ('theses-porto', 3, '%s %s/theses-porto.py' % (pythoncommand, lproc)),
        ('theses-dart', 4, '%s %s/theses-dart.py' % (pythoncommand, lproc)),
        ('4open', 3, '%s %s/edpjournals.py 4open %s 1' % (pythoncommand, lproc, pryear)),
        ('theses-wien', 2, '%s %s/theses-wien.py' % (pythoncommand, lproc)),
        ('theses-rostock', 3, '%s %s/theses-rostock.py' % (pythoncommand, lproc)),
        ('theses-texastech', 3, '%s %s/theses-texastech.py' % (pythoncommand, lproc)),
        ('theses-rochester', 2, '%s %s/theses-rochester.py' % (pythoncommand, lproc)),
        ('theses-colorado', 2, '%s %s/theses-colorado.py' % (pythoncommand, lproc)),
        ('information'  , 1,'%s %s/mdpi.sftp.py information' % (pythoncommand, lproc)),
        ('theses-buenosaires', 2, '%s %s/theses-buenosaires.py' % (pythoncommand, lproc)),
        #('theses-florida', 2, '%s %s/theses-florida.py' % (pythoncommand, lproc)),
        ('theses-syracuse', 3, '%s %s/theses-syracuse.py' % (pythoncommand, lproc)),
        ('theses-ncsu', 2, '%s %s/theses-ncsu.py' % (pythoncommand, lproc)),
        ('theses-oviedo', 3, '%s %s/theses-oviedo.py' % (pythoncommand, lproc)),
        ('theses-yorkcanada', 3, '%s %s/theses-yorkcanada.py' % (pythoncommand, lproc)),
        ('theses-alabama', 3, '%s %s/theses-alabama.py' % (pythoncommand, lproc)),
        ('theses-louisianastate', 3, '%s %s/theses-louisianastate.py' % (pythoncommand, lproc)),
        ('oapen', 1, '%s %s/oapen.py' % (pythoncommand, lproc)),
        ('theses-tsukuba', 3, '%s %s/theses-tsukuba.py' % (pythoncommand, lproc)),
        ('theses-rice', 3, '%s %s/theses-rice.py' % (pythoncommand, lproc)),
        ('npreview', 3, '%s %s/npreview.py %i %i' % (pythoncommand, lproc, pryear, prquarter)),
        ('integrablesystems', 12,'%s %s/oxfordjournals.xml.py integrablesystems %s 1' % (pythoncommand, lproc, pryear-2015)),
        ('theses-taiwannatlu', 2, '%s %s/theses-taiwannatlu.py' % (pythoncommand, lproc)),
        ('theses-virginia', 2, '%s %s/theses-virginia.py' % (pythoncommand, lproc)),
        ('theses-washingtonustlouis', 3, '%s %s/theses-washingtonustlouis.py' % (pythoncommand, lproc)),
        ('theses-swansea', 3, '%s %s/theses-swansea.py' % (pythoncommand, lproc)),
        ('theses-vanderbilt', 3, '%s %s/theses-vanderbilt.py' % (pythoncommand, lproc)),
        ('theses-wisconsinmadison', 3, '%s %s/theses-wisconsinmadison.py' % (pythoncommand, lproc)),
        ('theses-bristol', 3, '%s %s/theses-bristol.py' % (pythoncommand, lproc)),
        ('theses-royalholloway', 3, '%s %s/theses-royalholloway.py' % (pythoncommand, lproc)),
        ('theses-ucm', 2, '%s %s/theses-ucm.py' % (pythoncommand, lproc)),
        ('theses-coloradostate', 3, '%s %s/theses-coloradostate.py' % (pythoncommand, lproc)),
        ('theses-nottingham', 3, '%s %s/theses-nottingham.py' % (pythoncommand, lproc)),
        ('theses-cardiff', 3, '%s %s/theses-cardiff.py' % (pythoncommand, lproc)),
        ('theses-floridaintlu', 3, '%s %s/theses-floridaintlu.py' % (pythoncommand, lproc)),
        ('theses-olddominion', 3, '%s %s/theses-olddominion.py' % (pythoncommand, lproc)),
        ('theses-connecticut', 2, '%s %s/theses-connecticut.py' % (pythoncommand, lproc)),
        ('theses-hokkaido', 3, '%s %s/theses-hokkaido.py' % (pythoncommand, lproc)),
        ('theses-wisconsinmilwaukee', 3, '%s %s/theses-wisconsinmilwaukee.py' % (pythoncommand, lproc)),
        ('theses-hkust', 3, '%s %s/theses-hkust.py' % (pythoncommand, lproc)),
        ('theses-vrijeuamsterdam', 2, '%s %s/theses-vrijeuamsterdam.py' % (pythoncommand, lproc)),
        ('theses-regina', 3, '%s %s/theses-regina.py' % (pythoncommand, lproc)),
        ('theses-brussels', 2, '%s %s/theses-brussels.py' % (pythoncommand, lproc)),
        ('theses-ljubljana', 2, '%s %s/theses-ljubljana.py' % (pythoncommand, lproc)),
        ('theses-antwerp', 1, '%s %s/theses-antwerp.py' % (pythoncommand, lproc)),
        ('theses-conicet', 3, '%s %s/theses-conicet.py' % (pythoncommand, lproc)),
        ('theses-groningen', 3, '%s %s/theses-groningen.py' % (pythoncommand, lproc)),
        ('theses-kyushu', 2, '%s %s/theses-kyushu.py' % (pythoncommand, lproc)),
        ('theses-ankara', 3, '%s %s/theses-ankara.py' % (pythoncommand, lproc)),
        ('theses-new-mexico', 2, '%s %s/theses-new-mexico.py' % (pythoncommand, lproc)),
        ('theses-fub', 2, '%s %s/theses-fub.py' % (pythoncommand, lproc)),
        ('theses-auckland', 3, '%s %s/theses-auckland.py' % (pythoncommand, lproc)),
        ('theses-temple', 5, '%s %s/theses-temple.py' % (pythoncommand, lproc)),
        ('theses-tennessee', 3, '%s %s/theses-tennessee.py' % (pythoncommand, lproc)),
        ('theses-queensukingston', 2, '%s %s/theses-queensukingston.py' % (pythoncommand, lproc)),
        ('theses-estadoriodejaneiro', 2, '%s %s/theses-estadoriodejaneiro.py' % (pythoncommand, lproc)),
        ('theses-georgiatech', 3, '%s %s/theses-georgiatech.py' % (pythoncommand, lproc)),
        ('theses-marburg', 3, '%s %s/theses-marburg.py' % (pythoncommand, lproc)),
        ('theses-salamanca', 2, '%s %s/theses-salamanca.py' % (pythoncommand, lproc)),
        ('theses-kwazulu', 2, '%s %s/theses-kwazulu.py' % (pythoncommand, lproc)),
        ('theses-guelph', 3, '%s %s/theses-guelph.py' % (pythoncommand, lproc)),
        ('theses-potsdam', 1, '%s %s/theses-potsdam.py' % (pythoncommand, lproc)),
        ('techrxiv', 1, '%s %s/figshare.py techrxiv' % (pythoncommand, lproc)),
        ('theses-middleeasttech', 1, '%s %s/theses-middleeasttech.py' % (pythoncommand, lproc)),
        ('theses-wigner', 3, '%s %s/theses-wigner.py' % (pythoncommand, lproc)),
        ('theses-zaragoza', 3, '%s %s/theses-zaragoza.py' % (pythoncommand, lproc)),
        ('theses-melbourne', 3, '%s %s/theses-melbourne.py' % (pythoncommand, lproc)),
        ('theses-queensland', 1, '%s %s/theses-queensland.py' % (pythoncommand, lproc))]


if prmonth == 12:
    jnls.append(('OSAoe'  , 1, '%s %s/osa.py oe %i %i'  % (pythoncommand, lproc,pryear-1992, prmonth * 2 + 1)))
    jnls.append(('OSAoe'  , 1, '%s %s/osa.py oe %i %i'  % (pythoncommand, lproc,pryear-1992, prmonth * 2 + 2)))
    jnls.append(('apl'    , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924 + 1, 25)))
    jnls.append(('apl'    , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924 + 1, 26)))
    jnls.append(('procnas', 1, '%s %s/procnas.py %i 49,50' % (pythoncommand, lproc, pryear-1903)))
    jnls.append(('procnas', 1, '%s %s/procnas.py %i 51,52' % (pythoncommand, lproc, pryear-1903)))
#n    jnls.append(('fourier', 1, '%s %s/fourier.py %i %i'  % (pythoncommand, lproc, pryear-1950, 7)))
    jnls.append(('cag', 1, '%s %s/intlpress.py cag %i %i'  % (pythoncommand, lproc, pryear-1992, 7)))
    jnls.append(('cag', 1, '%s %s/intlpress.py cag %i %i'  % (pythoncommand, lproc, pryear-1992, 8)))
elif prmonth == 6:
    jnls.append(('apl'  , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924, 25)))
    jnls.append(('apl'  , 1, '%s %s/aip.xml2.py apl %i %i' % (pythoncommand, lproc, 2*pryear - 3924, 26)))

#work from 3th to 28th day of a month
def checkday(entrynumber):
    return (3 + (entrynumber % 26) == today.day)
    #return (5 + (entrynumber % 14) == today.day)
    #return (5 + (entrynumber % 24) == 5)

#writing to do list to protocol
prfil = open(protocol,"a")
print "previous month = %i/%i [today = %s]\n" % (prmonth,pryear, today.day)
prfil.write("---------{ %s }---{ running ejlwrapper.py for previous month %i/%i }---------\n will start the following commands:\n" % (stampoftoday, prmonth,pryear))
for entrynumber in range(len(jnls)):
    if (prmonth % jnls[entrynumber][1] == 0) and checkday(entrynumber):
        a=1
        prfil.write('  - '+jnls[entrynumber][2]+'\n')
prfil.close()

listofcommands = []

#report the jobs
for entrynumber in range(len(jnls)):
    if (prmonth % jnls[entrynumber][1] == 0) and checkday(entrynumber):
        listofcommands.append(jnls[entrynumber][2])
os.system('echo "%s" | mail -s "ejlwrapper commands"  florian.schwennsen@desy.de ' % ('\n '.join(listofcommands)))


prfil = open(protocol,"a")
prfil.write(' detailed protocols will be written to %s\n' % (logfile))
prfil.write(' has executed the following commands:\n')
prfil.close()



os.system("touch "+logfile)
#do always WSP

#do the jobs
for entrynumber in range(len(jnls)):
    if (prmonth % jnls[entrynumber][1] == 0) and checkday(entrynumber):
        print jnls[entrynumber]
        os.system("sleep 30 && "+jnls[entrynumber][2]+" >> "+logfile)
        #print "sleep 120 && "+jnls[entrynumber][2]+" >> "+logfile
        prfil = open(protocol,"a")
        prfil.write('  - '+jnls[entrynumber][2]+'\n')
        prfil.close()
        
#do always WSP or IOP or IEEE
prfil = open(protocol,"a")
if (today.day % 3 == 0):
    listofcommands.append('wsp.xml2.py')
    prfil.write('  - wsp.xml2.py\n')
    os.system('%s %s/wsp.xml2.py' % (pythoncommand, lproc))
elif (today.day % 3 == 1):
    listofcommands.append('ieee_wrapper.py')
    prfil.write('  - ieee_wrapper.py\n')
    os.system('%s %s/ieee_wrapper.py' % (pythoncommand, lproc))
if (today.weekday()  == 0):
    listofcommands.append('pubdbweb.py')
    prfil.write('  - pubdbweb.py\n')
    os.system('%s %s/pubdbweb.py' % (pythoncommand, lproc))

#do always IOP
#IOP books still old workflow
if (today.day % 7 == 0):
    listofcommands.append('iop.stacks.py')
    prfil.write('  - iop.stacks.py\n')
    os.system('%s %s/iop.stack.py' % (pythoncommand, lproc))
else:
    listofcommands.append('iop.sftp.py')
    prfil.write('  - iop.sftp.py\n')
    os.system('%s %s/iop.sftp.py' % (pythoncommand, lproc))

    
prfil.close()    

os.system('echo "%s" | mail -s "ejlwrapper finished"  florian.schwennsen@desy.de ' % ('\n '.join(listofcommands)))
os.system('echo "ejlwrapper finished" >> '+logfile)
prfil = open(protocol,"a")
prfil.write(' ejlwrapper.py has executed ALL commands.\n')
prfil.write("---------------------------------------------------------------------\n")
prfil.close()

#alldone = open('/tmp/alldone','w')
#alldone.write('\n\n\n\n************************************\n* ejlwrapper.py fuer Monat %2i/%4i *\n*      erfolgreich (?) beendet     *\n************************************\n' % (prmonth,pryear))
#alldone.close()
#os.system("lpr -Pl00ps5 /tmp/alldone")
