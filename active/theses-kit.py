# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from Karlsruhe Insitute of Technolgy
# FS 2020-01-13

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time 

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'KIT, Karlsruhe'

typecode = 'T'

jnlfilename = 'THESES-KIT-%s' % (stampoftoday)
pages = 25
years = 2

tocurl = 'https://primo.bibliothek.kit.edu/primo_library/libweb/action/search.do?ct=facet&rfnGrpCounter=8&rfnGrpCounter=7&indx=1&fn=search&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&dscnt=0&mode=Basic&vid=KIT&fctV=%5B2006+TO+null%5D&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&ct=facet&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Computational+Materials+Science+%28IAM-CMS%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Forschungsbereich+Troposph%C3%A4re+%28IMK-TRO%29&fctExcV=Institut+f%C3%BCr+Informationswirtschaft+und+Marketing+%28IISM%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Werkstoffkunde+%28IAM-WK%29&fctExcV=Institut+f%C3%BCr+Industriebetriebslehre+und+Industrielle+Produktion+%28IIP%29&fctExcV=Institut+f%C3%BCr+Produktionstechnik+%28WBK%29&fctExcV=Institut+f%C3%BCr+Angewandte+Biowissenschaften+%28IAB%29&fctExcV=Institut+f%C3%BCr+Fahrzeugsystemtechnik+%28FAST%29&fctExcV=Institut+f%C3%BCr+Mikrostrukturtechnik+%28IMT%29&fctExcV=Institut+f%C3%BCr+Bio-+und+Lebensmitteltechnik+%28BLT%29&fctExcV=Lichttechnisches+Institut+%28LTI%29&fctExcV=Institut+f%C3%BCr+Physikalische+Chemie+%28IPC%29&fctExcV=Institut+f%C3%BCr+Anthropomatik+und+Robotik+%28IAR%29&fctExcV=Institut+f%C3%BCr+Anorganische+Chemie+%28AOC%29&fctExcV=Institut+f%C3%BCr+Technische+Chemie+und+Polymerchemie+%28ITCP%29&fctExcV=Institut+f%C3%BCr+Angewandte+Informatik+und+Formale+Beschreibungsverfahren+%28AIFB%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Informatik+%28INFORMATIK%29&fctExcV=Institut+f%C3%BCr+Organische+Chemie+%28IOC%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Maschinenbau+%28MACH%29&fctExcV=Institut+f%C3%BCr+Unternehmungsf%C3%BChrung+%28IBU%29&fctExcV=Institut+f%C3%BCr+Angewandte+Geowissenschaften+%28AGW%29&fctExcV=Institut+f%C3%BCr+Technische+Mechanik+%28ITM%29&fctExcV=Institut+f%C3%BCr+Sport+und+Sportwissenschaft+%28IfSS%29&fctExcV=Institut+f%C3%BCr+Programmstrukturen+und+Datenorganisation+%28IPD%29&fctExcV=Institut+f%C3%BCr+Theoretische+Informatik+%28ITI%29&fctExcV=Institut+f%C3%BCr+Funktionelle+Grenzfl%C3%A4chen+%28IFG%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Werkstoff-+und+Biomechanik+%28IAM-WBM%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Atmosph%C3%A4rische+Umweltforschung+%28IMK-IFU%29&fctExcV=Institut+f%C3%BCr+Produktentwicklung+%28IPEK%29&fctExcV=Institut+f%C3%BCr+Mechanische+Verfahrenstechnik+und+Mechanik+%28MVM%29&fctExcV=Botanisches+Institut+und+Botanischer+Garten+%28BOTANIK%29&fctExcV=Engler-Bunte-Institut+%28EBI%29&fctExcV=Institut+f%C3%BCr+Toxikologie+und+Genetik+%28ITG%29&fctExcV=Institut+f%C3%BCr+Technik+der+Informationsverarbeitung+%28ITIV%29&fctExcV=Institut+f%C3%BCr+Nanotechnologie+%28INT%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Bauingenieur-%2C+Geo-+und+Umweltwissenschaften+%28BGU%29&fctExcV=Institut+f%C3%BCr+Thermische+Str%C3%B6mungsmaschinen+%28ITS%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Angewandte+Werkstoffphysik+%28IAM-AWP%29&fctExcV=Institut+f%C3%BCr+Technische+Informatik+%28ITEC%29&fctExcV=Institut+f%C3%BCr+Volkswirtschaftslehre+%28ECON%29&fctExcV=Institut+f%C3%BCr+Technikfolgenabsch%C3%A4tzung+und+Systemanalyse+%28ITAS%29&fctExcV=Institut+f%C3%BCr+Anthropomatik+%28IFA%29&fctExcV=Institut+f%C3%BCr+Analysis+%28IANA%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Atmosph%C3%A4rische+Spurenstoffe+und+Fernerkundung+%28IMK-ASF%29&fctExcV=Institut+f%C3%BCr+Mess-+und+Regelungstechnik+mit+Maschinenlaboratorium+%28MRT%29&fctExcV=Institut+f%C3%BCr+Hochfrequenztechnik+und+Elektronik+%28IHE%29&fctExcV=Institut+f%C3%BCr+Telematik+%28TM%29&fctExcV=Institut+f%C3%BCr+Kolbenmaschinen+%28IFKM%29&fctExcV=Zoologisches+Institut+%28ZOO%29&fctExcV=Institut+Kunst-+und+Baugeschichte+%28IKB%29&fctExcV=Institut+f%C3%BCr+Experimentelle+Teilchenphysik+%28ETP%29&fctExcV=Institut+f%C3%BCr+Informationsmanagement+im+Ingenieurwesen+%28IMI%29&fctExcV=Institut+f%C3%BCr+Thermische+Verfahrenstechnik+%28TVT%29&fctExcV=Institut+f%C3%BCr+Technische+Thermodynamik+und+K%C3%A4ltetechnik+%28ITTK%29&fctExcV=Institut+f%C3%BCr+Stochastik+%28STOCH%29&fctExcV=Institut+f%C3%BCr+Finanzwirtschaft%2C+Banken+und+Versicherungen+%28FBV%29&fctExcV=Institut+f%C3%BCr+Biomedizinische+Technik+%28IBT%29&fctExcV=Institut+f%C3%BCr+Angewandte+Betriebswirtschaftslehre+-+Unternehmensf%C3%BChrung+%28IBU%29&fctExcV=Institut+f%C3%BCr+Wasser+und+Gew%C3%A4sserentwicklung+%28IWG%29&fctExcV=Institut+f%C3%BCr+Massivbau+und+Baustofftechnologie+%28IMB%29&fctExcV=Institut+f%C3%BCr+Industrielle+Informationstechnik+%28IIIT%29&fctExcV=Institut+f%C3%BCr+Informationswirtschaft+und+-management+%28IISM%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Geistes-+und+Sozialwissenschaften+%28GEISTSOZ%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Elektrotechnik+und+Informationstechnik+%28ETIT%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Wirtschaftswissenschaften+%28WIWI%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Zuverl%C3%A4ssigkeit+von+Bauteilen+und+Systemen+%28IAM-ZBS%29&fctExcV=Institut+f%C3%BCr+Neutronenphysik+und+Reaktortechnik+%28INR%29&fctExcV=Institut+f%C3%BCr+Prozessdatenverarbeitung+und+Elektronik+%28IPE%29&fctExcV=Institut+f%C3%BCr+F%C3%B6rdertechnik+und+Logistiksysteme+%28IFL%29&fctExcV=Institut+f%C3%BCr+Prozessrechentechnik%2C+Automation+und+Robotik+%28IPR%29&fctExcV=Geophysikalisches+Institut+%28GPI%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Architektur+%28ARCH%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Chemie+und+Biowissenschaften+%28CHEM-BIO%29&rfnGrp=1&srt=date&tab=kit_evastar&fctN=facet_searchcreationdate&vl(freeText0)=istdissertation&dstmp=1582793145993&fctExcV=Institut%20f%C3%BCr%20Chemische%20Verfahrenstechnik%20(CVT)&mulExcFctN=facet_local12&rfnExcGrp=8&fctExcV=Elektrotechnisches%20Institut%20(ETI)&mulExcFctN=facet_local12&rfnExcGrp=8&fctExcV=Versuchsanstalt%20f%C3%BCr%20Stahl%2C%20Holz%20und%20Steine%20(VAKA)&mulExcFctN=facet_local12&rfnExcGrp=8&fctExcV=Fakult%C3%A4t%20f%C3%BCr%20Chemieingenieurwesen%20und%20Verfahrenstechnik%20(CIW)&mulExcFctN=facet_local12&rfnExcGrp=8&fctExcV=Institut%20f%C3%BCr%20Meteorologie%20und%20Klimaforschung%20(IMK)&mulExcFctN=facet_local12&rfnExcGrp=8'
tocurl = 'https://primo.bibliothek.kit.edu/primo_library/libweb/action/search.do?ct=search&rfnGrpCounter=9&fn=search&dscnt=1&vid=KIT&mode=Advanced&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Computational+Materials+Science+%28IAM-CMS%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Forschungsbereich+Troposph%C3%A4re+%28IMK-TRO%29&fctExcV=Institut+f%C3%BCr+Informationswirtschaft+und+Marketing+%28IISM%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Werkstoffkunde+%28IAM-WK%29&fctExcV=Institut+f%C3%BCr+Industriebetriebslehre+und+Industrielle+Produktion+%28IIP%29&fctExcV=Institut+f%C3%BCr+Produktionstechnik+%28WBK%29&fctExcV=Institut+f%C3%BCr+Angewandte+Biowissenschaften+%28IAB%29&fctExcV=Institut+f%C3%BCr+Fahrzeugsystemtechnik+%28FAST%29&fctExcV=Institut+f%C3%BCr+Mikrostrukturtechnik+%28IMT%29&fctExcV=Institut+f%C3%BCr+Bio-+und+Lebensmitteltechnik+%28BLT%29&fctExcV=Lichttechnisches+Institut+%28LTI%29&fctExcV=Institut+f%C3%BCr+Physikalische+Chemie+%28IPC%29&fctExcV=Institut+f%C3%BCr+Anthropomatik+und+Robotik+%28IAR%29&fctExcV=Institut+f%C3%BCr+Anorganische+Chemie+%28AOC%29&fctExcV=Institut+f%C3%BCr+Technische+Chemie+und+Polymerchemie+%28ITCP%29&fctExcV=Institut+f%C3%BCr+Angewandte+Informatik+und+Formale+Beschreibungsverfahren+%28AIFB%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Informatik+%28INFORMATIK%29&fctExcV=Institut+f%C3%BCr+Organische+Chemie+%28IOC%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Maschinenbau+%28MACH%29&fctExcV=Institut+f%C3%BCr+Unternehmungsf%C3%BChrung+%28IBU%29&fctExcV=Institut+f%C3%BCr+Angewandte+Geowissenschaften+%28AGW%29&fctExcV=Institut+f%C3%BCr+Technische+Mechanik+%28ITM%29&fctExcV=Institut+f%C3%BCr+Sport+und+Sportwissenschaft+%28IfSS%29&fctExcV=Institut+f%C3%BCr+Programmstrukturen+und+Datenorganisation+%28IPD%29&fctExcV=Institut+f%C3%BCr+Theoretische+Informatik+%28ITI%29&fctExcV=Institut+f%C3%BCr+Funktionelle+Grenzfl%C3%A4chen+%28IFG%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Werkstoff-+und+Biomechanik+%28IAM-WBM%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Atmosph%C3%A4rische+Umweltforschung+%28IMK-IFU%29&fctExcV=Institut+f%C3%BCr+Produktentwicklung+%28IPEK%29&fctExcV=Institut+f%C3%BCr+Mechanische+Verfahrenstechnik+und+Mechanik+%28MVM%29&fctExcV=Botanisches+Institut+und+Botanischer+Garten+%28BOTANIK%29&fctExcV=Engler-Bunte-Institut+%28EBI%29&fctExcV=Institut+f%C3%BCr+Toxikologie+und+Genetik+%28ITG%29&fctExcV=Institut+f%C3%BCr+Technik+der+Informationsverarbeitung+%28ITIV%29&fctExcV=Institut+f%C3%BCr+Nanotechnologie+%28INT%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Bauingenieur-%2C+Geo-+und+Umweltwissenschaften+%28BGU%29&fctExcV=Institut+f%C3%BCr+Thermische+Str%C3%B6mungsmaschinen+%28ITS%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Angewandte+Werkstoffphysik+%28IAM-AWP%29&fctExcV=Institut+f%C3%BCr+Technische+Informatik+%28ITEC%29&fctExcV=Institut+f%C3%BCr+Volkswirtschaftslehre+%28ECON%29&fctExcV=Institut+f%C3%BCr+Technikfolgenabsch%C3%A4tzung+und+Systemanalyse+%28ITAS%29&fctExcV=Institut+f%C3%BCr+Anthropomatik+%28IFA%29&fctExcV=Institut+f%C3%BCr+Analysis+%28IANA%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Atmosph%C3%A4rische+Spurenstoffe+und+Fernerkundung+%28IMK-ASF%29&fctExcV=Institut+f%C3%BCr+Mess-+und+Regelungstechnik+mit+Maschinenlaboratorium+%28MRT%29&fctExcV=Institut+f%C3%BCr+Hochfrequenztechnik+und+Elektronik+%28IHE%29&fctExcV=Institut+f%C3%BCr+Telematik+%28TM%29&fctExcV=Institut+f%C3%BCr+Kolbenmaschinen+%28IFKM%29&fctExcV=Zoologisches+Institut+%28ZOO%29&fctExcV=Institut+Kunst-+und+Baugeschichte+%28IKB%29&fctExcV=Institut+f%C3%BCr+Experimentelle+Teilchenphysik+%28ETP%29&fctExcV=Institut+f%C3%BCr+Informationsmanagement+im+Ingenieurwesen+%28IMI%29&fctExcV=Institut+f%C3%BCr+Thermische+Verfahrenstechnik+%28TVT%29&fctExcV=Institut+f%C3%BCr+Technische+Thermodynamik+und+K%C3%A4ltetechnik+%28ITTK%29&fctExcV=Institut+f%C3%BCr+Stochastik+%28STOCH%29&fctExcV=Institut+f%C3%BCr+Finanzwirtschaft%2C+Banken+und+Versicherungen+%28FBV%29&fctExcV=Institut+f%C3%BCr+Biomedizinische+Technik+%28IBT%29&fctExcV=Institut+f%C3%BCr+Angewandte+Betriebswirtschaftslehre+-+Unternehmensf%C3%BChrung+%28IBU%29&fctExcV=Institut+f%C3%BCr+Wasser+und+Gew%C3%A4sserentwicklung+%28IWG%29&fctExcV=Institut+f%C3%BCr+Massivbau+und+Baustofftechnologie+%28IMB%29&fctExcV=Institut+f%C3%BCr+Industrielle+Informationstechnik+%28IIIT%29&fctExcV=Institut+f%C3%BCr+Informationswirtschaft+und+-management+%28IISM%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Geistes-+und+Sozialwissenschaften+%28GEISTSOZ%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Elektrotechnik+und+Informationstechnik+%28ETIT%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Wirtschaftswissenschaften+%28WIWI%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Zuverl%C3%A4ssigkeit+von+Bauteilen+und+Systemen+%28IAM-ZBS%29&fctExcV=Institut+f%C3%BCr+Neutronenphysik+und+Reaktortechnik+%28INR%29&fctExcV=Institut+f%C3%BCr+Prozessdatenverarbeitung+und+Elektronik+%28IPE%29&fctExcV=Institut+f%C3%BCr+F%C3%B6rdertechnik+und+Logistiksysteme+%28IFL%29&fctExcV=Institut+f%C3%BCr+Prozessrechentechnik%2C+Automation+und+Robotik+%28IPR%29&fctExcV=Geophysikalisches+Institut+%28GPI%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Architektur+%28ARCH%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Chemie+und+Biowissenschaften+%28CHEM-BIO%29&fctExcV=Institut+f%C3%BCr+Chemische+Verfahrenstechnik+%28CVT%29&fctExcV=Elektrotechnisches+Institut+%28ETI%29&fctExcV=Versuchsanstalt+f%C3%BCr+Stahl%2C+Holz+und+Steine+%28VAKA%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Chemieingenieurwesen+und+Verfahrenstechnik+%28CIW%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+%28IMK%29&rfnGrp=1&tab=kit_evastar&dstmp=1627544151566&rfnGrpCounter=8&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=4&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=5&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=6&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=7&rfnExcGrp=8&rfnExcGrp=8&rfnExcGrp=8&rfnExcGrp=8&rfnExcGrp=8&fctV=%5B2006+TO+null%5D&ct=Next+Page&srt=date&fctN=facet_searchcreationdate&fctExcV=Institut%20f%C3%BCr%20Biologische%20Grenzfl%C3%A4chen%20(IBG)&mulExcFctN=facet_local12&rfnExcGrp=9&fctExcV=Institut%20f%C3%BCr%20Angewandte%20Materialien%20-%20Energiespeichersysteme%20(IAM-ESS)&mulExcFctN=facet_local12&rfnExcGrp=9&fctExcV=Institut%20f%C3%BCr%20Wirtschaftsinformatik%20und%20Marketing%20(IISM)&mulExcFctN=facet_local12&rfnExcGrp=9&fctExcV=Institut%20f%C3%BCr%20Katalyseforschung%20und%20-technologie%20(IKFT)&mulExcFctN=facet_local12&rfnExcGrp=9&fctExcV=KIT-Zentrum%20Klima%20und%20Umwelt%20(ZKU)&mulExcFctN=facet_local12&rfnExcGrp=9&vl(freeText0)=istdissertation&vl(freeText1)=&vl(freeText2)=&vl(90976954UI0)=any&vl(1UIStartWith0)=contains&vl(90976969UI1)=lsr16&vl(1UIStartWith1)=contains&vl(90977011UI2)=lsr48&vl(1UIStartWith2)=contains&vl(90977082UI3)=lsr42&vl(1UIStartWith3)=contains&vl(freeText3)=&vl(90977085UI4)=lsr17&vl(1UIStartWith4)=contains&vl(freeText4)=&vl(2273840UI5)=5-YEAR&vl(2273848UI6)=all_items'


recs = []
for i in range(pages):
    print '---{ %i }---' % (i)
    newrecs = []
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
        time.sleep(4)
    except:
        print "retry %s in 300 seconds" % (tocurl)
        time.sleep(300)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for div in tocpage.body.find_all('div', attrs ={'class' : 'EXLSummaryContainer'}):
        for h3 in div.find_all('h3', attrs ={'class' : 'EXLResultFourthLine'}):
            rec = {'jnl' : 'BOOK', 'tc' : 'T', 'note' : []}
            rec['year'] = h3.text.strip()
            rec['date'] = re.sub('.*?([12]\d\d\d).*', r'\1', h3.text.strip())
            for h2 in div.find_all('h2'):
                for a in h2.find_all('a'):
                    rec['artlink2'] = 'https://primo.bibliothek.kit.edu/primo_library/libweb/action/' + a['href']
                    rec['artlink'] = 'https://publikationen.bibliothek.kit.edu/' + re.sub('.*KITSRCE(\d+).*', r'\1', a['href'])
                    rec['tit'] = a.text.strip()
            if re.search('^\d+$', rec['year']):
                if int(rec['year']) >= now.year - years:
                    newrecs.append(rec)
            else:
                newrecs.append(rec)
                print '   ', rec['year'], '?'
    print '   %i+%i=%i recs' % (len(recs), len(newrecs), len(recs)+len(newrecs))
    recs += newrecs                            
    if newrecs or True:
        for a in tocpage.body.find_all('a', attrs ={'class' : 'EXLBriefResultsPaginationLinkNext'}):
            tocurl = a['href']
    else:
        break
    
        

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(4)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #abstract
            if meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #author
            elif meta['name'] == 'DC.Creator':
                rec['autaff'] = [[ meta['content'] ]]
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for table in artpage.body.find_all('table', attrs = {'class' : 'table'}):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) == 2:
                #Keywords
                if re.search('Schlagw', tds[0].text.strip()):
                    rec['keyw'] = re.split(', ', tds[1].text.strip())
                #Language
                elif tds[0].text.strip() == 'Sprache':
                    if tds[1].text.strip() != 'Englisch':
                        if tds[1].text.strip() == 'Deutsch':
                            rec['language'] = 'german'
                        else:
                            rec['language'] = tds[1].text.strip()
                #pages
                elif tds[0].text.strip() == 'Umfang':
                    if re.search('\d\d\d', tds[1].text.strip()):
                        rec['pages'] = re.sub('.*?(\d\d\d+).*', r'\1', tds[1].text.strip())
                #supervisor
                elif re.search('Betreuer', tds[0].text):
                    rec['supervisor'] = [[ re.sub('Prof\. ', '', re.sub('Dr\. ', '', tds[1].text.strip())) ]]
                #date
                elif re.search('Pr.fungsdatum', tds[0].text):
                    rec['MARC'] = [ ['500', [('a', 'Presented on ' + re.sub('(\d\d).(\d\d).(\d\d\d\d)', r'\3-\2-\1', tds[1].text.strip()))] ] ]
                #institue
                elif tds[0].text.strip() == 'Institut':
                    rec['note'].append(tds[1].text.strip())
                #urn
                elif tds[0].text.strip() == 'Identifikator':
                    for br in tds[1].find_all('br'):
                        br.replace_with('#')
                    for tdt in re.split('#',  re.sub('[\n\t\r]', '#', tds[1].text.strip())):
                        if re.search('urn:nbn', tdt):
                            rec['urn'] = re.sub('.*?(urn:nbn.*)', r'\1', tdt.strip())
    #license
    for a in artpage.body.find_all('a', attrs = {'class' : 'with-popover'}):
        if a.has_attr('data-content'):
            adc = a['data-content']
            if re.search('creativecommons.org', adc):
                rec['license'] = {'url' : re.sub('.*(http.*?) target.*', r'\1', adc)}                                        
    rec['autaff'][-1].append(publisher)
    if not 'doi' in rec.keys():
        if not 'urn' in rec.keys():
            rec['doi'] = '20.2000/KIT/' + re.sub('\D', '', rec['artlink'])
        rec['link'] = rec['artlink']
    print rec.keys()

    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
            
    
