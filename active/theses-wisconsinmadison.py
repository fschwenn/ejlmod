from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import ejlmod2
import os
import codecs
import datetime
import re

# Initialize webdriver
driver = webdriver.PhantomJS()

recs = []

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Wisconsin, Madison (main)'
jnlfilename = 'THESES-WISCONSINMADISON-%s' % (stampoftoday)
departments = [(5, 'Physics', '', 'Wisconsin U., Madison'),
               (3, 'Mathematics', 'm', 'Wisconsin U., Madison, Math. Dept.')]

def get_author(header):
    name, forename, author = header[0].find_all('span', attrs={'class', 'author'})[0].text.replace('\n', '').split(',')

    return forename + " " + name


def get_sub_side(link, fc, aff):
    rec = {'keyw' : [], 'note' : []}
    print "[" + link + "] --> Harvesting Data"
    driver.get(link)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    header = soup.find_all('div', attrs={'class', 'titles'})
    rec['tit'] = header[0].find_all('h1')[0].text.replace('\n', '')  # Insert Title



    for div in soup.find_all('div', attrs = {'id' : 'acc-pub'}):
        for div2 in div.find_all('div'):
            dtt = ''
            for dt in div2.find_all('dt'):
                dtt = dt.text.strip()
            for dd in div2.find_all('dd'):
                if dtt == 'Creator':
                    rec['autaff'] = [[ re.sub('^by ', '', dd.text.strip()), publisher ]]
                elif dtt == 'Publication':
                    rec['date'] = dd.text.strip()
                elif dtt == 'Physical Details':
                    if re.search('\d\d+ leaves', dd.text):
                        rec['pages'] = re.sub('.*?(\d\d+) leaves.*', r'\1', dd.text.strip())

    # Get the abstract
    for div in soup.find_all('div', attrs = {'id' : 'show-more-dtls'}):
        rec['abs'] = div.text.strip()


    # Get Notes section
    if len(soup.find_all('div', attrs={'class', 'accordion-conten'})) > 0:
        for note in soup.find_all('div', attrs={'class', 'notes_list'})[0].find_all('li'):
            if note.text[0:len('Advisor')] == "Advisor":
                advisor = note.text.split(': ')[1]
                rec['supervisor'] = [[advisor[0:len(advisor) - 1]]]
    else:
        rec['supervisor'] = [['']]
    rec['link'] = link
    rec['jnl'] = 'BOOK'
    rec['doi'] = '20.2000/WisconsinMadison/' + re.sub('\W', '', link[31:])
    rec['tc'] = 'T'

    if fc:
        rec['fc'] = 'm'

    #keywords and date type from staff page
    sleep(1)
    driver.get(link + '/staff')
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    for tr in soup.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'tag'}):
            tag = td.text.strip()
            td.decompose()
        if tag in ['653', '502']:
            for td in tr.find_all('td'):
                for span in td.find_all('span'):
                    span.decompose()
                if tag == '653':
                    rec['keyw'].append(re.sub(' *\.$', '', td.text.strip()))
                elif tag == '502':
                    rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', td.text.strip())

    recs.append(rec)
        


def get_index_page(url, fc, aff):
    # Get Index page
    driver.get(url)

    index_links = BeautifulSoup(driver.page_source, 'lxml').find_all('a', attrs={'class', 'item_path'})
    for i in index_links:
	#print '[https://search.library.wisc.edu'+i.get('href')+'] --> Harvesting data'
        get_sub_side("https://search.library.wisc.edu" + i.get('href'), fc, aff)
        sleep(10)


for (pages, dep, fc, aff) in departments:
    for page in range(1, pages+1):
        print dep + " --- Open Page " + str(page) + " ---"
        get_index_page("https://search.library.wisc.edu/search/system/browse?filter%5Bfacets%5D%5Bsubjects_facet"
                       "~Dissertations%2C+Academic%5D=yes&filter%5Bfacets%5D%5Bsubjects_facet~" + dep + "%5D=yes&page=" +
                       str(page) + "&sort=newest", fc, aff)
        sleep(10)


# Save data in xml file
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
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
