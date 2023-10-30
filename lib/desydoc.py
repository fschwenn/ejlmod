#!/usr/bin/python
# if no other argument is given, mails of the last three days are checked
######## Moduls ###################################################
import os, sys, string, imaplib, email, re
from email import Parser
from ftplib import FTP
import time, datetime
import ssh # support for ssh login for libi1
import zipfile
#import poplib
import subprocess
from inspire_harvesting import inspire_harvesting
import unicodedata 
import codecs
import tarfile

######### How many days should be checked ? ######################
if len(sys.argv) > 1:
    try:
        scope = int(sys.argv[1])
    except:
        scope = 7
else:
    scope = 7
######### Paths & Definitions #####################################
ejlpath = "/afs/desy.de/user/l/library/dok/ejl"
noup_ieee = "/afs/desy.de/group/library/publisherdata/ieee/noupd"
publisherpath = "/afs/desy.de/group/library/publisherdata"
protocol = "/afs/desy.de/group/library/publisherdata/log/protocol"
procpath = "/afs/desy.de/user/l/library/proc"
proc3path = "/afs/desy.de/user/l/library/proc/python3"
iop_stacks = "/afs/desy.de/group/library/publisherdata/iop"
xslt_path = "/afs/desy.de/user/l/library/proc/altova"
inspire_ejlpath = "/afs/desy.de/user/l/library/inspire/ejl"
ftppath = "/afs/desy.de/group/library/preprints/incoming"

day = str(time.localtime().tm_yday)
date = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

#python from virtualenv "inspire" on inspire3.desy.de
pythoncommand = '/home/library/.virtualenvs/inspire/bin/python'
python3command = '/home/library/.virtualenvs/inspire3-python3.8/bin/python'

py_err = re.compile('.*Error:')
##################################################################

###### Part of source code ######################################
# write protocol
if not os.path.exists(protocol):
    os.system("touch %s" %protocol)
proto = open(protocol,"a")
startstr = 40*"#" + 2*"\n" +"Starting Cron-Job for day %s\n" % date
proto.write(startstr)
####################################################################


########### support Functions ################################################

def error(errnr):
    """returns error messages"""
    err = {"err0"  : "can`t connect to server!\n",
           "err1"  : "can`t connect to Mailbox!\n",
           "err2"  : "can`t download file!\n", 
           "err3"  : "script iop.py problems!\n", 
           "err4"  : "script ieee.py problems!\n",
           "err5"  : "script else.py problems\n!",
           "err6"  : "script springer.py problems!\n", 
           "err7"  : ": does not exist- printing aborted\n",
           "err8"  : "cant login\n",
           "err9"  : "cant download file\n", 
           "err10" : "cant unzip file\n",
           "err11" : "was already downloaded, so i do nothing\n",
           "err12" : "script wsp.py problems!\n",
           "err13" : "stylesheet problems\n", 
           "err14" : "unzip problems\n", 
           "err15" : "script nuovocimento.xml.py problems!\n" }
    return err[errnr]


def dateconv(email_date):
    """converts email_date into epoch-time"""
    # email_time can be i.e. Wed, 17 Jul 2009 14:42:32 +0000 or 17 Jul 2009 13:13:23
    signs = ["," , "+", "-", "UT", "GMT"]
    for sign in signs:
        ind = email_date.find(sign)
        if ind == -1:continue # no - + , in email_time
        if sign == ",":    email_date = email_date[ind +1:]
        else: email_date = email_date[:ind]
        print email_date
    try:
        strptime = time.strptime(email_date, " %d %b %Y %H:%M:%S ")
    except:
        strptime = time.strptime(email_date, "%d %b %Y %H:%M:%S ")
    return time.mktime(strptime)

def timehandle(email_date,day=2.0):
    """only emails to convert which not older than day (default 2 days)"""
    diff = datetime.datetime.today() - datetime.timedelta(days=day)    #timedelta to covert pdfs which are older than some days
    diff = time.mktime(diff.timetuple()) #epoch time
    email_time = dateconv(email_date) #epoch time
        #FS 12-06-20: wait two days
        #FS 12-12-10: wait three days
        #    if email_time >= diff: #comparing epoch times
    heute = time.mktime(datetime.datetime.now().timetuple())
    latency = 3 * 86400 * 0
    if (email_time >= diff-latency) and (email_time <= heute-latency): #comparing epoch times
            return "todo"
    else: return "dontdo"

def download_ftp(ftp,filename):
    """download file from ftp server"""
    f2 = open(filename,"wb")
    try:
        ftp.retrbinary("RETR " + filename,f2.write)
        proto.write("%s downloaded succesful\n" %filename)
    except Exception:
        proto.write(error("err9"))
        return "bad"
    f2.close()
    return "ok"

def ssh_inspire(cmd):
    """logs in as library on libi1 and executes commands"""
    (pid, tty) = ssh.rlogin("inspire", "library", "XXX")
    time.sleep(1.0)
    ssh.execute(tty,cmd)
    time.sleep(1.0)
    ssh.rlogout(tty)
    time.sleep(1.0)
    os.waitpid(pid, 0)#gets sure all child processes are finished
    return



def check_email(all_data,msg,text_data):
    """decides if iop, else, springer, ieee, wsp, aip"""
    # msg is a dictionary of the email header with keys:
    #['Received', 'Received', 'Received', 'Received', 'Received', 'Received', 'Received', 'Received', 'Received',
    # 'X-Spam-Virus', 'X-Spam-TaggedAsSpamByDesy', 'X-Spam-Checker-Version', 'X-Spam-Level', 'X-Spam-Status', 'X-desy-gw-Envelope-From',
    #'Message-ID', 'MIME-Version', 'Content-Type', 'Content-Transfer-Encoding', 'From', 'To', 'Date', 'Subject', 'User-Agent', 'Return-Path', 'X-OriginalArrivalTime']
    #
    # text_data is the body of the message
    #
    # all_data[0][1] contains both header and body in one string

    #[FS] more compact
    ## search_term: (wo, publisher, function)
    tododictionary = {'<journals@aip-info.org>' : ("From", "AIP", aipnew),
                      "springer" : ("From", "SPRINGER", springer),
                      'content.management@hindawi.com' : ('From', 'Hindawi', hindawi),
                      "AIP Conference" : ("From", "AIP", aip),
                      "APPB" : ("Subject","APPB",appb),
                      "Acta Physica Polonica B" : ("Subject","APPB",appb),
                      "Acta Physica Polonica A" : ("Subject","APPA",appa),
#blocked                      "<WileyOnlineLibrary@wiley.com>" : ("From", "WILEY", wiley),                      
                      'newsletter@updates.cambridge.org': ("From", 'CUP', cambridge),
                      "@sif.it" : ("From", "Nuovo Cimento", nuovocimento),
                      "Frontiers in " : ("Subject", "Frontiers", frontiers),
                      "Grobid" : ("Subject", "publisher", grobid)
                      }
#    tododictionary = {"springer" : ("From", "SPRINGER", springer)}
    for todo in tododictionary:
        if todo in msg[tododictionary[todo][0]]:
            print tododictionary[todo][1]
            proto.write("processing email from %s -- %s\n" % (tododictionary[todo][1],msg["Date"]))
            try:
                tododictionary[todo][2](msg,all_data,text_data)
            except:
                proto.write("errors in automatik %s-module\n" % (tododictionary[todo][1]))
            proto.write(40*"-" + "\n")
    return





def run_xslt_cmd(publisher_xslt_path,saxon_path,org_xml_path):
    """execute the stylesheet on publisher xml"""
    os.chdir("/afs/desy.de/user/l/library/inspire/ejl") #jump into inspire_ejlpath directory (this is important, because the stylesheet generate dynamic outputfiles in the main directory)
    cmd = '/usr/bin/java -jar %s -s:"%s" %s' %(saxon_path,org_xml_path,publisher_xslt_path) #use always full paths (script runs in cron)
    os.system(cmd) #execute xslt processing



def search_springer_xml(arg,dirname,names):
        """This function is ment to work with os.path.walk. it runs in subdirectories of springerpath and starts the xslt engine on every *.xml"""
        if "JournalOnlineFirst" in dirname: return #no OF
        for name in names:
                org_xml_path = os.path.join(dirname,name)
                if not org_xml_path.endswith(".xml"): continue
                #run_xslt_cmd(arg[0],arg[1],org_xml_path)


#FS create big xml and write to ret
#createinspirexml((['/afs/...,...],'oxford','ptep2013.6')
def tfstrip(x): return x.strip()
def createinspirexml(xmlfiles,publisher,dokfilename):
    intermediateversion = '-1.25'
    finalxml = os.path.join(inspire_ejlpath,dokfilename+".xml")
    publisher_xslt_path = os.path.join(xslt_path,publisher + intermediateversion + ".xslt")
    intermediate_xslt_path = os.path.join(xslt_path,'intermediate' + intermediateversion + ".xslt")
    saxon_path = os.path.join(xslt_path,"saxon9he.jar") # saxon xslt processor
    inspirexmlfiles = []

    print 'will try to convert the following files to',finalxml
    print xmlfiles

    for xmlfile in xmlfiles:
        basename = re.sub('.*\/','',xmlfile)
        print "\n--- %s ---\n" % (basename)

        os.system('/usr/bin/java -jar %s -s:%s -xsl:%s  -o:/tmp/i%s' % (saxon_path,xmlfile,publisher_xslt_path,basename))
        os.system('/usr/bin/java -jar %s -t -s:/tmp/i%s -xsl:%s' % (saxon_path,basename,intermediate_xslt_path))
        #get doi
        inf = open('/tmp/i%s' % (basename),'r')
        lines = ' '.join(map(tfstrip,inf.readlines()))
        inf.close()
        dois = re.findall('<doi> *<content>(10.*?)<',lines)
        for doi in dois:
            doi1 = re.sub('[\(\)\/]','_',doi)
            inspirexmlfiles.append(os.path.join(inspire_ejlpath,doi1+".xml"))
        #process = subprocess.Popen(['/usr/bin/java','-jar',saxon_path,'-t','-s:/tmp/i'+basename,'-xsl:'+intermediate_xslt_path], stdout=subprocess.PIPE)
        #process.wait()
        #output,stderr = process.communicate()
        #print ">>>",output
        #for line in output:
        #    print '-',line
        #    if re.search('Writing to',line): inspirexmlfiles.append(re.sub('.*(\/afs.*xml).*',r'\1',line.strip()))
        #inspirexmlfiles.append(re.search('(\/afs.*xml)',output).group())
        print inspirexmlfiles
    os.system("cat %s > /tmp/final.xml " % (' '.join(inspirexmlfiles)))
    os.system("grep -v '<collection' /tmp/final.xml|grep -v '<\/collection'|grep -v '<.xml version'|grep -v 'xmlns:xsi=.http'|grep -v 'xsi:schemaLocation=' > /tmp/final2.xml")
    os.system("echo '<collection>' > %s " % (finalxml))
    os.system("cat /tmp/final2.xml >> %s " % (finalxml))
    os.system("echo '</collection>' >> %s " % (finalxml))
    os.system("echo %s >> %s " % (finalxml,os.path.join(procpath,'retinspire','retfiles')))
    return finalxml


################################################################

#######################################################
############## functions for publisher ################
def nuovocimento(msg,all_data,text_data):
    sifpath = os.path.join(publisherpath, "sif")
    os.chdir(sifpath)
    message = email.message_from_string(all_data[0][1])
    message.is_multipart()
    payloads = message.get_payload()
    proto.write("email has %i attachment\n" % (len(payloads)-1))
    zipfiles = []
    #deleting all files in PUB-dirs
    #try:
    #    os.system("rm -rf *zip XM*")
    #except:
    #    pass
    #download zip files
    try:
        for attachment in payloads[1:]:
            #print attachment
            print attachment.get_filename()
            zipfiles.append(attachment.get_filename())
            zipfile = open(os.path.join(sifpath, attachment.get_filename()), 'w')
            zipfile.write(attachment.get_payload(decode=1))
            zipfile.close()
            proto.write("    zipfile downloaded\n")
    except:
        proto.write(error("err2"))
    #unzip zipfiles
    for zipfile in zipfiles:
        proto.write('    process %s\n' % (zipfile))
        try:
            os.system("rm -rf *xml")
            os.system('unzip %s' % (zipfile))
            time.sleep(1)
            os.system('mv XM*/*xml .')
        except:
            proto.write(error("err14"))
        try:
            argument = re.sub('.(zip|ZIP)', '  ', zipfile)
            for xmlfile in os.listdir(sifpath):
                if re.search('xml$', xmlfile) and not os.path.isfile('%s/done/%s' % (sifpath, xmlfile)):
#                if re.search('xml$', xmlfile):
                    argument += re.sub('.xml$', ' ', xmlfile)
            command = '%s %s/nuovocimento.xml.py %s' % (pythoncommand, procpath, argument)
            proto.write('         '+command+'\n')
            fi, foe = os.popen4('ssh inspire3')
            print >>fi, command
            fi.close ()
            text = foe.read()
            foe.close()
            if (py_err.search(text)):
                proto.write("errors in nuovocimento.xml.py\n")
            else: 
                proto.write("nuovocimento.xml.py run on inspire3 correct\n")
        except:
            proto.write(error("err15"))
    return

def appa(msg,all_data,text_data):
    appapath =  os.path.join(publisherpath,"appa")
    os.chdir(appapath)
    message = email.message_from_string(all_data[0][1])
    message.is_multipart()
    payloads = message.get_payload()
    proto.write("email has %i attachment\n" % (len(payloads)-1))
    print "email has %i attachment\n" % (len(payloads)-1)
    xmlfiles = []
    #deleting all files in PUB-dirs
    try:
        os.system("rm -r  *xml*")
    except:
        pass
    try:
        for attachment in payloads[1:]:
            #print attachment
            filename = 'appa_'+attachment.get_filename()
            print filename
            proto.write("  attachment:%s\n" % (filename))
            if os.path.isfile(os.path.join(appapath,'done',filename)):
                proto.write("    already in done\n")
            else:
                publisherxml = open(os.path.join(appapath,filename),'wb')
                publisherxml.write(attachment.get_payload(decode=1))
                publisherxml.close()
                proto.write("    attachment downloaded\n")
                xmlfiles.append(os.path.join(appapath,filename))
    except:
        proto.write(error("err2"))
    for xmlfile in xmlfiles:
        prog = os.path.join(procpath,"crossref.py")
        if re.search('\.xml$', xmlfile):
            fi, foe = os.popen4('ssh inspire3')
            print >>fi, '%s %s %s' % (pythoncommand, prog, xmlfile)
            fi.close ()
            text = foe.read()
            foe.close()
            if (py_err.search(text)):
                proto.write("errors in crossref.py %s\n" % (xmlfile))
            else: 
                proto.write("crossref.py run on inspire3 correct\n")
        else:
            os.system('cd %s && unzip %s' % (appapath, xmlfile))
            for xmlfile2 in os.listdir(appapath):
                if re.search('\.xml$', xmlfile2):
                    print 'python %s %s/%s' % (prog, appapath, xmlfile2)
                    fi, foe = os.popen4('ssh inspire3')
                    print >>fi, 'python %s %s/%s' % (prog, appapath, xmlfile2)
                    fi.close ()
                    text = foe.read()
                    foe.close()
                    if (py_err.search(text)):
                        proto.write("errors in crossref.py %s\n" % (xmlfile2))
                    else: 
                        proto.write("crossref.py run on inspire3 correct\n")                        
        os.system("mv %s %s" % (os.path.join(appapath, xmlfile), os.path.join(appapath, 'done')))
        os.system('rm %s/*.xml' % (appapath))
    return


def grobid(msg,all_data,text_data):
    message = email.message_from_string(all_data[0][1])
    message.is_multipart()
    payloads = message.get_payload()
    proto.write("email has %i attachment\n" % (len(payloads)-1))
    try:
        if 1 > 0:
            for attachment in payloads[1:]:
                filename = attachment.get_filename()
                print filename
                proto.write("  attachment:%s\n" % (filename))
                #get tar-file
                publishertar = open(os.path.join('/tmp', filename), mode='wb')
                publishertar.write(attachment.get_payload(decode=1))
                publishertar.close()
                #find name of xml
                for line in text_data.split("\n"):
                    if re.search('grobid\.split.*\.xml', line):
                        publisherxml = re.sub('.*(grobid\.split.*?\.xml).*', r'\1', line.strip())
                        break
                #extract tar-file
                publishertar = tarfile.open(os.path.join('/tmp', filename), 'r')
                publishertar.extract(publisherxml, path=ftppath)
                publishertar.close()
                #add pseudo-DOI to xml
                xmlfile = codecs.EncodedFile(codecs.open(os.path.join(ftppath, publisherxml), mode='rb'), 'utf8')
                lines = xmlfile.readlines()
                xmlfile.close()
                xmlfile = codecs.EncodedFile(codecs.open(os.path.join(ftppath, publisherxml), mode='wb'), 'utf8')
                counter = 1
                for line in lines:
                    xmlfile.write(line)
                    if re.search('<record>', line):
                        xmlfile.write('  <datafield tag="024" ind1="7" ind2=" ">\n')
                        xmlfile.write('    <subfield code="a">44.4444/%s_%04i</subfield>\n' % (publisherxml, counter))
                        xmlfile.write('    <subfield code="2">NODOI</subfield>\n  </datafield>\n')
                        counter += 1
                xmlfile.close()
                send_text = inspire_harvesting(publisherxml, 'grobid')
                if send_text:
                    proto.write(send_text)
    except:
        proto.write("errors in grobid")
    return






    
def appb(msg,all_data,text_data):
    appbpath =  os.path.join(publisherpath,"appb")
    os.chdir(appbpath)
    #print all_data[0][1].lower()
    #if "content-disposition: attachment" in all_data[0][1].lower():
    message = email.message_from_string(all_data[0][1])
    message.is_multipart()
    payloads = message.get_payload()
    proto.write("email has %i attachment\n" % (len(payloads)-1))
    xmlfiles = []
    #deleting all files in PUB-dirs
    try:
        os.system("rm -r  *xml*")
    except:
        pass
    try:
        for attachment in payloads[1:]:
            #print attachment
            filename = 'appb'+attachment.get_filename()
            print filename
            proto.write("  attachment:%s\n" % (filename))
            if os.path.isfile(os.path.join(appbpath,'done',filename)):
                proto.write("    already in done\n")
            else:
                xmlfiles.append(os.path.join(appbpath,filename))
                #print '>1',os.path.join(appbpath,filename)
                publisherxml = open(os.path.join(appbpath,filename+'t'),'wb')
                publisherxml.write(attachment.get_payload(decode=1))
                publisherxml.close()
                #dirty workaround
                publisherxmlt = open(os.path.join(appbpath,filename+'t'),'r')
                publisherxml = open(os.path.join(appbpath,filename),'wb')
                for line in publisherxmlt.readlines():
                    publisherxml.write(line)
                    if re.search('<\/doi_batch>',line):
                        break
                publisherxml.close()
                publisherxmlt.close()
                proto.write("    attachment downloaded\n")
    except:
        proto.write(error("err2"))
    #translate to INSPIRE-xml
    for xmlfile in xmlfiles:
        if re.search('.xml$', xmlfile):
            try:             
                fi, foe = os.popen4('ssh inspire3')
                prog = os.path.join(procpath,"crossref.py")
                print >>fi, 'python %s %s' % (prog, xmlfile)
                fi.close ()
                text = foe.read()
                foe.close()
                if (py_err.search(text)):
                    proto.write("errors in crossref.xml.py\n")
                    proto.write(text)
                else: 
                    proto.write("crossref.py run on inspire3 correct\n")
                os.system("mv %s %s" % (xmlfile,os.path.join(appbpath,'done')))
            except:
                proto.write("errors in crossref.xml.py !\n")
    return


def frontiers(msg,all_data,text_data):
    message = email.message_from_string(all_data[0][1])
    tokenfile = '%s/frontiers/done/frontiers-email-%s' % (publisherpath, re.sub('\W', '_', message['Date']))
    if os.path.isfile(tokenfile):
        print ' %s already done' % (tokenfile)
        return
    chunksize = 25
    prog = os.path.join(procpath, "frontiers.py")
    reclick = re.compile('.*?(http..*click.engage.frontiersin.*?qs=.*?)".*')
    restart = re.compile('class.*tableArticlesHeading')
    urls = []
    print '--{Frontiers}--'
    message = re.sub('\n', '', re.sub('=\r\n', '', text_data))
    lines = re.split('<\/', message)
    started = False
    for line in lines:
        if restart.search(line):
            started = True
        elif started:
            if reclick.search(line):
                urls.append(re.sub('=3D', '=', reclick.sub(r'\1', line)))
    #print len(urls)
    numofchunks = (len(urls)-1) / chunksize + 1
    print len(urls), numofchunks
    try:
        proto.write(' > python %s' % (prog))
        for i in range(numofchunks):
            print '--{ %i/%i }--' % (i+1, numofchunks)
            #print '"%s"' % ('" "'.join(urls[i*chunksize:(i+1)*chunksize]))
            fi, foe = os.popen4('ssh inspire3')
            print >>fi, '%s %s "%s"' % (pythoncommand, prog, '" "'.join(urls[i*chunksize:(i+1)*chunksize]))
            fi.close()
            text = foe.read()
            foe.close()
        if (py_err.search(text)):
            proto.write("python errors in frontiers.py\n")
        else: 
            proto.write("frontiers.py run on inspire3 correct\n")
            os.system('touch %s' % (tokenfile))
    except:
        proto.write("errors in frontiers.py\n")     
    return

def ptep(msg,all_data,text_data):
    pteppath = os.path.join(publisherpath,"oup")
    os.chdir(pteppath)
    try: #connecting to springer
        ftp = FTP("ftp.highwire.org")
        proto.write("Connection to Server ftp.highwire.org succesfull\n")
    except:
        proto.write(error("err0"))
        return
    try:
        ftp.login("XXX","XXX")
        proto.write("Login as ftpinspires on ftp.highwire.org succesfull\n")
    except:
        proto.write(error("err8"))
        return
    #dirname = os.path.join(ftp.pwd(),"ptep")
    #try:
    #    ftp.cwd(dirname)
    #except:
    #    print 'could not enter directory "ptep"'
    # deleting all files in PUB-dirs
    try:
        os.system("rm -r *tar *xml")
    except:
        pass
    #get filename
    message = all_data[0][1]
    if re.search('ptep\/', message):
        filename = re.sub('^ptep.','',re.search('ptep\/.*gz',message).group())
    elif re.search('pasj\/', message):
        filename = re.sub('^pasj.','',re.search('pasj\/.*gz',message).group())
    print 'will download',filename,'\n'
    #test if file was already downloaded
    done = os.path.join(pteppath,"done",filename)
    if os.path.exists(done):
        proto.write(done + error("err11"))
        return
    print "downloading file %s from OUP\n" % filename
    status = download_ftp(ftp,filename)
    if status == "bad": return
    time.sleep(1.0)
    try:
        os.system("tar xzf %s" %os.path.join(pteppath,filename))
        time.sleep(0.5)
        os.system("tar xf *TagTextFiles.tar")
        os.system("mv %s done" %os.path.join(pteppath,filename))
        proto.write("unzip file succesfull\n")
    except:
        proto.write("err10")
        return
    #list of single xml-files
    time.sleep(1.0)
    xmlfiles = []
    for xmlfilename in os.listdir(pteppath):
        if re.search('\.xml$',xmlfilename):
            xmlfiles.append(os.path.join(pteppath,xmlfilename))
    #translate to INSPIRE-xml
    createinspirexml(xmlfiles,'oxford',re.sub('\..*','',filename))
    return

        
def hindawi(msg,all_data,text_data):
    """processes Hindawi-emails"""
    timestamp = time.strftime("%j-%H%M", time.localtime())
    hindawipath = os.path.join(publisherpath,"hindawi")
    os.chdir(hindawipath)
    try: #connecting to hindawi
        ftp = FTP("ftp.hindawi.com")
        proto.write("Connection to Server ftp.springer-dds.com succesfull\n")
    except:
        proto.write(error("err0"))
        return
    try:
        ftp.login("XXX", "XXX")
        proto.write("Login as INSPIRE on ftp.hindawi.comsuccesfull\n")
    except:
        proto.write(error("err8"))
        return
    files = ftp.nlst()  
    filenames = files[-10:]
    todo = 0
    for filename in filenames:
        #test if file was already downloaded
        done = os.path.join(hindawipath,"done",filename)
        if not re.search('zip$', filename):
            proto.write('skip "%s" (not a proper zip-file)' % (filename))
            continue
        if os.path.exists(done):
            proto.write(done + error("err11"))
        else:
            print "downloading file %s from Hindawi\n" % filename
            status = download_ftp(ftp,filename)
            if status == "bad":
                continue
            time.sleep(1.0)
            todo = 1
    if todo == 0:
        return
    else:
        try:
            fi, foe = os.popen4('ssh inspire3')
            prog = os.path.join(procpath,"hindawi.ftp.py")
            print >>fi, 'source /usr/bin/virtualenvwrapper.sh'
            print >>fi, 'workon inspire'
            print >>fi, 'python %s %s' % (prog,timestamp)
            fi.close ()
            text = foe.read()
            foe.close()
            if (py_err.search(text)):proto.write("errors in hindawi.ftp.py\n")
            else: proto.write("hindawi.ftp.py run on inspire3 correct\n")
        except:
            proto.write(error("err6"))
    return

def springer(msg,all_data,text_data):
    """processes springer-emails"""
    timestamp = time.strftime("%j-%H%M", time.localtime())
    springerpath = os.path.join(publisherpath,"springer")
    #springerpath = testpath
    os.chdir(springerpath)
    try: #connecting to springer
        ftp = FTP("ftp.springer-dds.com")
        proto.write("Connection to Server ftp.springer-dds.com succesfull\n")
    except:
        proto.write(error("err0"))
        return
    try:
        ftp.login("XXX","XXX")
        proto.write("Login as ftpdes on ftp.springer-dds.com succesfull\n")
    except:
        proto.write(error("err8"))
        return

    path = os.path.join("data", "in")
    dirname = os.path.join(ftp.pwd(),path)
    ftp.cwd(dirname)
    files = ftp.nlst()  #list of the zip.files from springer
    filenames = files[-10:] #last entry

    # deleting all files in PUB-dirs
    os.system("rm -r JOU*/* BSE*/*")
    # deleting some files in springerpath
    for direc in os.listdir(springerpath):
        file = os.path.join(springerpath,direc)
        if file.endswith("ret") or file.endswith("retout") or file.startswith("xa"): os.remove(file)
    todo = 0
    for filename in filenames:
        #test if file was already downloaded
        done = os.path.join(springerpath,"done",filename)
        if not re.search('ftp.*zip', filename):
            continue
            if filename != "JATS Samples":
                proto.write('skip "%s" (not a proper zip-file)\n' % (filename))
        if os.path.exists(done):
            proto.write(done + error("err11"))
            continue
        print "downloading file %s from Springer\n" % filename
        status = download_ftp(ftp,filename)
        if status == "bad": continue
        time.sleep(1.0)
        try:
            os.system("unzip -n %s" %os.path.join(springerpath,filename))
            os.system("mv %s done" %os.path.join(springerpath,filename))
            proto.write("unzip file succesfull\n")
        except:
            proto.write("err10")
            continue
        todo = 1
    if todo == 0: return # if no new springer-files do nothing
    try:
        fi, foe = os.popen4('ssh inspire3')
        prog = os.path.join(procpath,"springer.nlm.py")
        print >>fi, 'source /usr/bin/virtualenvwrapper.sh'
        print >>fi, 'workon inspire'
        print >>fi, 'python %s %s' % (prog,timestamp)
        fi.close ()
        text = foe.read()
        foe.close()
        if (py_err.search(text)):proto.write("errors in springer.nlm.py\n")
        else: proto.write("springer.nlm.py run on inspire3 correct\n")

    except:
        proto.write(error("err6"))
    return

        
def cambridge(msg,all_data,text_data):
    """Cambridge journals"""
    prog = os.path.join(procpath, "cambridge.py")    
    for line in re.split('<a', ''.join(re.sub('=3D', '=', re.sub('(=\r|\n|\t)', '', text_data)))):
        if re.search('<div class="title">.*olume.*ssue', line):
            cont = re.sub('.*<div class="title">(.*?)<.*', r'\1', line.strip())
            jid = re.sub(' .*', '', cont)
            vol = re.sub('.*olume (\d+).*', r'\1', cont)
            issue = re.sub('.*ssue (\d+).*', r'\1', cont)
            donefile = '%s/cambridge/done/%s.%s.%s' % (publisherpath, jid, vol, issue)
            if not os.path.isfile(donefile):
                try:
                    proto.write(' > %s %s %s %s\n' % (prog, jid, vol, issue))
                    fi, foe = os.popen4('ssh inspire2')
                    print >>fi, 'python %s %s %s %s' % (prog, jid, vol, issue)
                    fi.close()
                    text = foe.read()
                    foe.close()
                    if (py_err.search(text)):proto.write("errors in cambridge.py\n")
                    else: 
                        proto.write("cambridge.py run on inspire2 correct\n")
                        os.system('touch %s' % (donefile))
                except:
                    proto.write("errors in cambridge.py\n")
    return
    

def wiley(msg,all_data,text_data):
    """handles Wiley journals"""
    wileydict = {'Fortschr. Phys.' : 'fortp',
                 'Ann. Phys.' : 'annphys',
                 'Astron. Nachr.' : 'asnaa',
                 'Comm. Pure Appl. Math.' : 'cpama',
                 'Fortschritte der Physik' : 'fortp',
                 'Annalen der Physik' : 'annphys',
                 'Astronomische Nachrichten' : 'asnaa',
                 'Advanced Quantum Technologies' : 'aqt',
                 'Quantum Engineering' : 'quanteng',
                 'Mathematische Nachrichten' : 'mana',
                 'physica status solidi (a)' : 'pssa',
                 'physica status solidi (RRL) - Rapid Research Letters' : 'pssr',
                 'International Journal of Quantum Chemistry' : 'qua',
                 'Communications on Pure and Applied Mathematics' : 'cpama'}                 
    #prog = os.path.join(procpath, "wiley.xml2.py")
    prog = os.path.join(proc3path, "wiley3.py")
    if not re.search('New Articles', msg["Subject"]) and not re.search('Early View', msg["Subject"]) and not re.search('These new articles', msg["Subject"]):
        subj = re.sub('\n', ' ', re.sub('.*Contents? Alert: *', '', msg["Subject"]))
        journal = re.sub('. Rapid', '- Rapid', re.sub(',? Vol.*', '', subj))
        vol = re.sub('.*?(\d+),.*', r'\1', subj)
        issue = re.sub('.*?Vol.*?, .*?(\d+\-?\d*).*', r'\1', subj)
        year = re.sub('.*?No.*?(20\d\d).*', r'\1', subj)
        print msg["Subject"]
        print  '%s|%s|%s|%s' % (journal, vol, issue, year)
        if wileydict.has_key(journal):
            jnl = wileydict[journal]
            donefile = '%s/wiley/done/%s.%s.%s' % (publisherpath, jnl, vol, issue)
            if not os.path.isfile(donefile):
                try:
                    proto.write(' > %s %s %s %s %s %s\n' % (python3command, prog, jnl, vol, issue, year))
                    print '%s %s %s %s %s %s' % (python3command, prog, jnl, vol, issue, year)
                    fi, foe = os.popen4('ssh inspire3')
                    print >>fi, '%s %s %s %s %s %s' % (python3command, prog, jnl, vol, issue, year)
                    fi.close()
                    text = foe.read()
                    foe.close()
                    if (py_err.search(text)):proto.write("errors in wiley3.py\n")
                    else: 
                        proto.write("wiley3.py run on inspire3 correct\n")
                        os.system('touch %s' % (donefile))
                except:
                    proto.write("errors in wiley3.py\n")
    return

def aipnew(msg,all_data,text_data):
    """handles AIP journals"""
    aipdict = {'Journal of Mathematical Physics' : 'jmp',
               'Review of Scientific Instruments' : 'rsi',
               'Chaos' : 'chaos',
               'American Journal of Physics' : 'ajp',
               'Low Temperature Physics' : 'ltp'}
    prog = os.path.join(procpath, "aip.xml2.py")
    journal = re.sub('.*" *(.*?) *".*', r'\1', msg["From"])
    journal = re.sub(' <journals.*> *', '', journal)
    if aipdict.has_key(journal):
        jnl = aipdict[journal]
        for line in text_data.split("\n"):
            if re.search('Volume \d+, Issue \d+', line):
                vol = re.sub('.*Volume (\d+).*', r'\1', line)
                issue = re.sub('.*Issue (\d+).*', r'\1', line)
                break
        donefile = '%s/aip/done/%s.%s.%s' % (publisherpath, jnl, vol, issue)
        if not os.path.isfile(donefile):
            try:
                proto.write(' > python %s %s %s %s\n' % (prog, jnl, vol, issue))
                fi, foe = os.popen4('ssh inspire3')
                print >>fi, '%s %s %s %s %s' % (pythoncommand, prog, jnl, vol, issue)
                fi.close()
                text = foe.read()
                foe.close()
                if (py_err.search(text)):proto.write("errors in aip.xml2.py\n")
                else: 
                    proto.write("aip.xml2.py run on inspire3 correct\n")
                    os.system('touch %s' % (donefile))
            except:
                proto.write("errors in aip.xml.py\n")             
    else:
        proto.write(" unknown AIP journal %s\n" % (journal))
    return
                 

def aip(msg,all_data,text_data):
    """handles aip conference proceedings"""
    prog = os.path.join(procpath, "aipcp_check_relevance.py")
    aippath = '/afs/desy.de/group/library/publisherdata/aip/done'

    vol = re.sub('.*?Volume (\d\d\d\d), Issue \d.*', r'\1', msg["Subject"])
    iss = re.sub('.*?Volume \d\d\d\d, Issue (\d).*', r'\1', msg["Subject"])
    aipconf = os.path.join(aippath, 'aipcp%s.%s.all' % (vol, iss))
    if os.path.exists(aipconf):
        proto.write("aipcp%s.%s already exists: so i do nothing\n" % (vol, iss))
        return
    try:
        fi, foe = os.popen4('ssh inspire3')
        print >>fi, '%s %s %s %s' % (pythoncommand, prog, vol, iss)
        fi.close ()
        text = foe.read()
        foe.close()
        if (py_err.search(text)): proto.write("errors in aipcp_check_relevance.py\n")
        else: proto.write("aipcp_check_relevance.py was executed\n")
    except:
        proto.write("aipcp_check_relevance.py was not executed\n")
        return

def main():
    """main function"""
    try:
        srv = imaplib.IMAP4_SSL("mail.desy.de", 993)
        proto.write("Connection to Server ximap.desy.de succesfull\n")
    except:
        proto.write(error("err0"))
        sys.exit()
    try:
        srv.login("desydoc", "XXX")
        proto.write("Login on mail desydoc@desy.de succesfull\n")
    except:
        proto.write(error("err1"))
        sys.exit()
    proto.write(40*"-" + "\n")

    srv.select() #default is inbox
    typ, data = srv.search(None, 'ALL') #all messages
    #typ, data = srv.search(None, '(UNSEEN)') #only unseen messages

    #first fetch all mails, then go through them
    #instead of starting scripts right away and risking to loose
    #contact to the mail server
    allmails = []    
    for num in data[0].split():
        #all data
        #print 'my Message |%s|\ndata:|%s|\n' % (num,data[0])
        try: typ, all_data = srv.fetch(num, '(RFC822)')
        except:
            try: srv.close()
            except: pass
            proto.write("Imaplib.error: Reconecting to MAilServer.\n")
            main()
        #print 'Message %s\n%s\n' % (num, all_data[0][1])

        #text data
        try:
            data1 = srv.fetch(num, '(BODY[TEXT])')
            text_data = data1[1][0][1]
            #print "Message %s\n%s\n" %(num,text_data)
        except:
            text_data = ""

        #header data
        try:
            data = srv.fetch(num, '(BODY[HEADER])')
            header_data = data[1][0][1]
        except:
            print "Fetching HEADER failed - continue"
            continue
        #einzelzugriff auf header inhalte

        msg = Parser.HeaderParser().parsestr(header_data)
        #test = Parser.Parser().parsestr(all_data[0][1])
        #print test
        email_date = msg["Date"]
        print email_date
        check = timehandle(email_date,scope) #only emails not older then 'scope' day

        if not check == "todo" : continue
        print 20*"#"
        print "Message %s" %num
#KAOS        for i in msg.keys():
#KAOS             print "%s: %s" %(i,msg[i])

        ###starttime = datetime.datetime.now()

        ###check_email(all_data,msg,text_data)
        allmails.append((all_data, msg, text_data))
        #print text_data


    srv.close() 

    #now check mails
    i = 0 
    for (all_data, msg, text_data) in allmails:
        i += 1
        print '---{ %i/%i }---{ %s }---{ %s }---' % (i, len(allmails), msg['From'], msg['Subject'])
        check_email(all_data,msg,text_data)
    #check_ejl() # checks if same dok-files in ejl and in ejl/backup
####################################################
if __name__ == "__main__":
    main()
    #check_ejl()
