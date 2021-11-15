# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest OUP-journals
# FS 2015-01-26

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
def fsunwrap(tag):
    try: 
        for em in tag.find_all('em'):
            cont = em.string
            em.replace_with(cont)
    except:
        print 'fsunwrap-em-problem'
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

publisher = 'Oxford University Press'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

if len(sys.argv) > 4:
    jnlfilename = '%s%s.%s_%s' % (jnl, vol, issue, sys.argv[4])
else:
    jnlfilename = '%s%s.%s' % (jnl, vol, issue)

if   (jnl == 'rpd'): 
    issn = '1742-3406'
    jnlname = 'Radiat.Prot.Dosim.'
elif (jnl == 'ptep'):
    issn = ' 2050-3911'
    jnlname = 'PTEP'
elif (jnl == 'mnras'): 
    jnlname = 'Mon.Not.Roy.Astron.Soc.'
elif (jnl == 'mnrasl'): 
    jnlname = 'Mon.Not.Roy.Astron.Soc.'
elif (jnl == 'pasj'): 
    jnlname = "Publ.Astron.Soc.Jap."
elif (jnl == 'qjmath'): 
    jnlname = "Quart.J.Math.Oxford Ser."
elif (jnl == 'bjps'): 
    jnlname = "Brit.J.Phil.Sci."
elif (jnl == 'imrn'): 
    jnlname = "Int.Math.Res.Not."
elif (jnl == 'nsr'):
    jnlname = "Natl.Sci.Rev."
elif (jnl == 'astrogeo'):
    jnlname = 'Astron.Geophys.'
elif (jnl == 'integrablesystems'):
    jnlname = 'J.Integrab.Syst.'
    
else:
    print 'Dont know journal %s!' % (jnl)
    sys.exit(0)


ptepcollcode = {'A0' : 'General physics', 'A00' : 'Classical mechanics', 'A01' : 'Electromagentism',
                'A02' : 'Other topics in general physics', 'A1' : 'Mathematical physics', 'A10' : 'Integrable systems and exact solutions',
                'A11' : 'Solitons', 'A12' : 'Rigorous results', 'A13' : 'Other topics in mathematical physics',
                'A2' : 'Computational physics', 'A20' : 'The algorithm of numerical calculations', 'A21' : 'Numerical diagonalization',
                'A22' : 'Monte-Carlo simulations', 'A23' : 'Molecular dynamics simulations', 'A24' : 'Other numerical methods',
                'A3' : 'Nonlinear dynamics', 'A30' : 'Dynamical systems', 'A31' : 'The other dynamical systems such as cellular-automata and coupled map lattices',
                'A32' : 'Quantum chaos', 'A33' : 'Classical chaos', 'A34' : 'Other topics in nonlinear dynamics',
                'A4' : 'Statistical mechanics - equilibrium systems', 'A40' : 'Critical phenomena, phase diagrams, phase transitions', 'A41' : 'Spin-glass, random spins',
                'A42' : 'Classical spins', 'A43' : 'Quantum spins', 'A44' : 'Neural networks',
                'A45' : 'Informational statistical physics', 'A46' : 'Quantum statistical mechanics', 'A47' : 'Other topics in equilibrium statistical mechanics',
                'A5' : 'Statistical mechanics - nonequilibrium systems', 'A50' : 'Stochastic processes, stochastic models and percolations', 'A51' : 'Relaxations, hysteresis, response, transport in classical systems',
                'A52' : 'Transport of quantum systems', 'A53' : 'Reaction-diffusion systems', 'A54' : 'Pattern formation, fracture, self-organizations',
                'A55' : 'Synchronization; coupled oscillators', 'A56' : 'Nonlinear and nonequilibrium phenomena', 'A57' : 'Nonequilibrium steady states',
                'A58' : 'Other topics in nonequilibrium statistical mechanics', 'A6' : 'Quantum physics', 'A60' : 'Foundation of quantum mechanics',
                'A61' : 'Quantum information', 'A62' : 'Quantum phase transition', 'A63' : 'Quantum many-body systems',
                'A64' : 'Other topics in quantum mechanics', 'A7' : 'Thermodynamics and thermodynamic processes', 'A70' : 'Mathematical theory of thermodynamics',
                'A71' : 'Molecular motors', 'A72' : 'Energy transfers in biological systems', 'A73' : 'Other thermal processes',
                'B0' : 'Gauge field theories', 'B00' : 'Lattice gauge field theories', 'B01' : 'Spontaneous symmetry breaking',
                'B02' : 'Confinement', 'B03' : 'Chern Simons theories', 'B04' : 'Quantization and formalism',
                'B05' : 'Other topics in gauge field theories', 'B1' : 'Supersymmetry', 'B10' : 'Extended supersymmetry',
                'B11' : 'Supergravity', 'B12' : 'Supersymmetry breaking', 'B13' : 'Supersymmetry phenomenology',
                'B14' : 'Dynamics of supersymmteric gauge theories', 'B15' : 'Supersymmetric quantum mechanics', 'B16' : 'Supersymmetric field theory',
                'B17' : 'Other topics in supersymmetry', 'B2' : 'String theory', 'B20' : 'String duality',
                'B21' : 'AdS/CFT correspondence', 'B22' : 'Black holes in string theory', 'B23' : 'Brane and its dynamics',
                'B24' : 'CFT approach in string theory', 'B25' : 'M theory, matrix theory', 'B26' : 'Tachyon condensation',
                'B27' : 'Topological field theory', 'B28' : 'String field theory', 'B29' : 'Other topics in string theory',
                'B3' : 'Quantum field theory', 'B30' : 'General', 'B31' : 'Symmetries and anomalies',
                'B32' : 'Renormalization and renormalization group equation', 'B33' : 'Field theories in higher dimensions', 'B34' : 'Field theories in lower dimensions',
                'B35' : 'Solitons, monopoles and instantons, 1/N expansion', 'B36' : 'Composite states and effective theories', 'B37' : 'Various models of field theory',
                'B38' : 'Lattice field theories', 'B39' : 'Quantization and formalism', 'B4' : 'Model building',
                'B40' : 'Beyond the Standard Model', 'B41' : 'Compactification and string', 'B42' : 'Grand unified theories',
                'B43' : 'Models with extra dimensions', 'B44' : 'Technicolor and composite models', 'B45' : 'Unified models with gravity',
                'B46' : 'Other topics in model building', 'B5' : 'Weak interactions and related phenomena', 'B50' : 'Electromagnetic processes and properties',
                'B51' : 'B, D, K physics', 'B52' : 'CP violation', 'B53' : 'Higgs physics',
                'B54' : 'Neutrino physics', 'B55' : 'Quark masses and Standard Model parameters', 'B56' : 'Rare decays',
                'B57' : 'Standard Model', 'B58' : 'Supersymmetric Standard Model', 'B59' : 'Other topics in weak interactions and related phenomena',
                'B6' : 'Strong interactions and related phenomena', 'B60' : 'Chiral lagrangians', 'B61' : 'Deep inelastic scattering',
                'B62' : 'Hadronic colliders', 'B63' : 'Jets', 'B64' : 'Lattice QCD',
                'B65' : 'Perturbative QCD', 'B66' : 'Spin and polarization effects', 'B67' : 'Sum rules',
                'B68' : 'Holographic approach to QCD', 'B69' : 'Other topics in strong interactions and related phenomena', 'B7' : 'Astroparticle physics',
                'B70' : 'Baryogenesis', 'B71' : 'Dark matter', 'B72' : 'Inflation',
                'B73' : 'Cosmology of theories beyond the Standard Model', 'B74' : 'High energy cosmic rays', 'B75' : 'Solar and atmospheric neutrinos',
                'B76' : 'Thermal field theory', 'B77' : 'Other topics in astroparticle physics', 'B8' : 'Mathematical methods',
                'B80' : 'Differential and algebraic geometry', 'B81' : 'Integrable systems', 'B82' : 'Noncommutative geometry',
                'B83' : 'Matrix models', 'B84' : 'Quantum groups', 'B85' : 'Bethe ansatz, exact S-matrix',
                'B86' : 'Statistical methods, random systems', 'B87' : 'Other topics in mathematical methods', 'C0' : 'Standard Model and related topics',
                'C00' : 'Quantum chromodynamics', 'C01' : 'Electroweak model, Higgs bosons, electroweak symmetry breaking', 'C02' : 'Cabibbo-Kobayashi-Maskawa quark-mixing matrix',
                'C03' : 'CP violation', 'C04' : 'Neutrino masses, mixing, and oscillations', 'C05' : 'Quark model',
                'C06' : 'Structure functions, fragmentation functions', 'C07' : 'Particle properties', 'C08' : 'Tests of conservation laws',
                'C09' : 'Other topics', 'C1' : 'Hypothetical particles and concepts', 'C10' : 'Supersymmmetry',
                'C11' : 'Dynamical electroweak symmetry breaking', 'C12' : 'Grand unified theories', 'C13' : 'Searches for quark and lepton compositeness',
                'C14' : 'Extra dimensions', 'C15' : 'Axions', 'C16' : 'Free quark searches',
                'C17' : 'Magnetic monopoles', 'C18' : 'Heavy vector bosons', 'C19' : 'Other topics',
                'C2' : 'Collider experiments', 'C20' : 'Hadron collider experiments', 'C21' : 'Lepton collider experiments',
                'C22' : 'Electron-proton collider experiments', 'C23' : 'Other topics', 'C3' : 'Experiments using particle beams',
                'C30' : 'Experiments using hadron beams', 'C31' : 'Experiments using charged lepton beams', 'C32' : 'Experiments using neutrino beams',
                'C33' : 'Experiments using photon beams', 'C34' : 'Other topics', 'C4' : 'Non-accelerator experiments',
                'C40' : 'Experiments using RI source', 'C41' : 'Laser experiments', 'C42' : 'Reactor experiments',
                'C43' : 'Underground experiments', 'C44' : 'Other topics', 'C5' : 'Other topics in experimental particle physics',
                'C50' : 'Other topics in experimental particle physics', 'D0' : 'Fundamental interactions and nuclear properties', 'D02' : 'Weak interactions in nuclear system',
                'D03' : 'Electromagnetic interactions in nuclear system', 'D04' : 'Nuclear matter and bulk properties of nuclei', 'D05' : 'Few-body problems in nuclear system',
                'D06' : 'Effective interactions in nuclear system', 'D1' : 'Nuclear structure', 'D10' : 'Nuclear many-body theories',
                'D11' : 'Models of nuclear structure', 'D12' : 'General properties of nuclei --- systematics and theoretical analysis', 'D13' : 'Stable and unstable nuclei',
                'D14' : 'Hypernuclei', 'D15' : 'Mesic nuclei and exotic atoms', 'D2' : 'Nuclear reactions and decays',
                'D20' : 'General reaction theories', 'D21' : 'Models of nuclear reactions', 'D22' : 'Light ion reactions',
                'D23' : 'Heavy-ion reactions', 'D24' : 'Photon and lepton reactions', 'D25' : 'Hadron reactions',
                'D26' : 'Fusion, fusion-fission reactions and superheavy nuclei', 'D27' : 'Reactions induced by unstable nuclei', 'D28' : 'Relativistic heavy-ion collisions',
                'D29' : 'Nuclear decays and radioactivities', 'D3' : 'Quarks, hadrons and QCD in nuclear physics', 'D30' : 'Quark matter',
                'D31' : 'Quark-gluon plasma', 'D32' : 'Hadron structure and interactions', 'D33' : 'Hadrons and quarks in nuclear matter',
                'D34' : 'Lattice QCD calculations in nuclear physics', 'D4' : 'Nuclear astrophysics', 'D40' : 'Nucleosynthesis',
                'D41' : 'Nuclear matter aspects in nuclear astrophysics', 'D42' : 'Nuclear physics aspects in explosive environments', 'D5' : 'Other topics in nuclear physics',
                'D50' : 'Other topics in nuclear physics', 'E0' : 'Gravity', 'E00' : 'Gravity in general',
                'E01' : 'Relativity', 'E02' : 'Gravitational waves', 'E03' : 'Alternative theory of gravity',
                'E04' : 'Higher-dimensional theories', 'E05' : 'Quantum gravity', 'E1' : 'Basic astrophysical processes',
                'E10' : 'Astrophysical processes in general', 'E11' : 'Radiative processes and thermodynamics', 'E12' : 'Chemical and nuclear reactions',
                'E13' : 'Kinetic theory and plasma', 'E14' : 'Hydrodynamics and magnetohydrodynamics', 'E15' : 'Relativistic dynamics',
                'E16' : 'Stellar dynamics', 'E2' : 'Stars and stellar systems', 'E20' : 'Stars and stellar systems in general',
                'E21' : 'The sun and solar system', 'E22' : 'Exoplanets', 'E23' : 'Interstellar matter and magnetic fields',
                'E24' : 'Star formation', 'E25' : 'Stellar structure and evolution', 'E26' : 'Supernovae',
                'E27' : 'Galaxies and clusters', 'E28' : 'Extragalactic medium and fields', 'E3' : 'Compact objects 　',
                'E30' : 'Compact objects in general', 'E31' : 'Black holes', 'E32' : 'Neutron stars',
                'E33' : 'Pulsars', 'E34' : 'Accretion, accretion disks', 'E35' : 'Relativistic jets',
                'E36' : 'Massive black holes', 'E37' : 'Gamma ray bursts', 'E38' : 'Physics of strong fields',
                'E4' : 'Cosmic rays and neutrinos', 'E40' : 'Cosmic rays and neutrino in general', 'E41' : 'Cosmic rays',
                'E42' : 'Acceleration of particles', 'E43' : 'Propagation of cosmic rays', 'E44' : 'Cosmic gamma rays',
                'E45' : 'Neutrinos', 'E5' : 'Large scale structure of the universe', 'E50' : 'Large scale structure in general',
                'E51' : 'Superclusters and voids', 'E52' : 'Statistical analysis of large scale structure', 'E53' : 'Large scale structure formation',
                'E54' : 'Semi-analytic modeling', 'E55' : 'Cosmological simulations', 'E56' : 'Cosmological perturbation theory',
                'E6' : 'Observational cosmology', 'E60' : 'Observational cosmology in general', 'E61' : 'Cosmometry',
                'E62' : 'Gravitational lensing', 'E63' : 'Cosmic background radiations', 'E64' : 'Dark energy and dark matter',
                'E65' : 'Probes of cosmology', 'E7' : 'Particle cosmology', 'E70' : 'Particle cosmology in general',
                'E71' : 'Big bang nucleosynthesis', 'E72' : 'Baryon asymmetry', 'E73' : 'Cosmological phase transitions and topological defects',
                'E74' : 'Cosmology of physics beyond the Standard Model', 'E75' : 'Physics of the early universe', 'E76' : 'Quantum field theory on curved space',
                'E8' : 'Inflation and cosmogenesis', 'E80' : 'Inflation and cosmology in general', 'E81' : 'Inflation',
                'E82' : 'Alternative to inflation', 'E83' : 'String theory and cosmology', 'E84' : 'Extra dimensions',
                'E85' : 'Transplanckian physics', 'E86' : 'Quantum cosmology', 'F0' : 'Cosmic ray particles',
                'F00' : 'Instrumentation and technique', 'F01' : 'Earth-Solar system and Heliosphere', 'F02' : 'Origin, composition, propagation and interactions of cosmic rays',
                'F03' : 'Ultra-high energy phenomena of cosmic rays', 'F04' : 'Other topics', 'F1' : 'Photons',
                'F10' : 'Instrumentation and technique', 'F11' : 'Radiation from galactic objects', 'F12' : 'Radiation from extragalactic objects',
                'F13' : 'High energy and non-thermal phenomena', 'F14' : 'Cosmic microwave background and extragalactic background lights', 'F15' : 'Other topics',
                'F2' : 'Neutrino', 'F20' : 'Instrumentation and technique', 'F21' : 'Solar, atmospheric and earth-originated neutrinos',
                'F22' : 'Neutrinos from supernova remnant and other astronomical objects', 'F23' : 'Neutrino mass, , mixing, oscillation and interaction', 'F24' : 'Other topics',
                'F3' : 'Gravitational wave', 'F30' : 'Instrumentation and technique', 'F31' : 'Expectation and estimation of gravitational radiation',
                'F32' : 'Calibration and operation of gravitational wave detector', 'F33' : 'Network system, coincident signal in other radiation bands', 'F34' : 'Other topics',
                'F4' : 'Dark matter, dark energy and particle physics', 'F40' : 'Instrumentation and technique', 'F41' : 'Laboratory experiments',
                'F42' : 'Observational result on astrophysical phenomena', 'F43' : 'Interpretation and explanation of observation and experiment', 'F44' : 'Cosmology, early universe and quantum gravity',
                'F45' : 'Other topics', 'G0' : 'Accelerators', 'G00' : 'Colliders',
                'G01' : 'Light sources', 'G02' : 'Ion accelerators', 'G03' : 'Electron accelerators',
                'G04' : 'Beam sources', 'G05' : 'Accelerator components', 'G06' : 'Accelerator design',
                'G07' : 'Others', 'G1' : 'Physics of beams', 'G10' : 'Beam dynamics',
                'G11' : 'Beam instabilities and cures', 'G12' : 'Beam measurement and manipulation', 'G13' : 'Interaction of beams',
                'G14' : 'Novel acceleration scheme', 'G15' : 'Accelerator theory', 'G16' : 'Others',
                'G2' : 'Application of beams', 'G20' : 'Scientific application', 'G21' : 'Medical application',
                'G22' : 'Industrial application', 'G23' : 'Others', 'H0' : 'General issue for instrumentation',
                'H00' : 'Interaction of radiation with matter', 'H01' : 'Concepts of the detector', 'H02' : 'Simulation and detector modeling',
                'H03' : 'Radiation damage/hardness', 'H04' : 'Dosimetry and apparatus', 'H1' : 'Detectors, apparatus and methods for the physics using accelerators',
                'H10' : 'Experimental detector systems', 'H11' : 'Gaseous detectors', 'H12' : 'Semiconductor detectors',
                'H13' : 'Calorimeters', 'H14' : 'Particle identification', 'H15' : 'Photon detectors',
                'H16' : 'Neutrino detectors', 'H17' : 'Instrumentation for medical, biological and materials research', 'H2' : 'Detectors, apparatus and methods for non-accelerator physics',
                'H20' : 'Instrumentation for underground experiments', 'H21' : 'Instrumentation for ground observatory', 'H22' : 'Instrumentation for space observatory',
                'H3' : 'Detector readout concepts, electronics, trigger and data acquisition methods', 'H30' : 'Electronic circuits', 'H31' : 'Front-end electronics',
                'H32' : 'Microelectronics', 'H33' : 'Digital Signal Processor', 'H34' : 'Data acquisition',
                'H35' : 'Trigger', 'H36' : 'Online farm and networking', 'H37' : 'Control and monitor systems',
                'H4' : 'Software and analysis related issue for instrumentation', 'H40' : 'Computing, data processing, data reduction methods', 'H41' : 'Image processing',
                'H42' : 'Pattern recognition, cluster finding, calibration and fitting methods', 'H43' : 'Software architectures', 'H5' : 'Engineering and technical issues',
                'H50' : 'Detector system design, construction technologies and materials', 'H51' : 'Manufacturing', 'H52' : 'Detector alignment and calibration methods',
                'H53' : 'Detector cooling and thermo-stabilization', 'H54' : 'Gas systems and purification', 'H55' : 'Machine detector interface',
                'I0' : 'Structure, mechanical and acoustical properties', 'I00' : 'Structure of liquids and solids', 'I01' : 'Equations of state',
                'I02' : 'Phase equilibria and phase transitions', 'I03' : 'Lattice dynamics and crystal statistics', 'I04' : 'Mechanical properties',
                'I05' : 'Defects', 'I06' : 'Liquid crystals', 'I07' : 'Acoustical properties',
                'I08' : 'Other topics', 'I1' : 'Thermal properties and nonelectronic transport properties', 'I10' : 'Thermal properties',
                'I11' : 'Thermal transport', 'I12' : 'Ionic transport', 'I13' : 'Liquid metal',
                'I14' : 'Other topics', 'I2' : 'Quantum fluids and solids', 'I20' : 'Liquid and solid helium',
                'I21' : 'Supersolid', 'I22' : 'Quantum states of cold gases', 'I23' : 'Other topics',
                'I3' : 'Low dimensional systems -nonelectronic properties', 'I30' : 'Surfaces, interfaces and thin films', 'I31' : 'Clusters',
                'I32' : 'Graphene, fullerene', 'I33' : 'Nanotube, nanowire', 'I34' : 'Quantum dot',
                'I35' : 'Other nanostructures', 'I36' : 'Other topics', 'I4' : 'Electron states in condensed matter',
                'I40' : 'Metal', 'I41' : 'Semiconductor', 'I42' : 'Organics',
                'I43' : 'd- and f- electron systems', 'I44' : 'First-principles calculations', 'I45' : 'Mott transitions',
                'I46' : 'Strong correlations', 'I47' : 'Other topics', 'I5' : 'Electronic transport properties',
                'I50' : 'Disordered systems, Anderson transitions', 'I51' : 'Hall effect', 'I52' : 'Magnetoresistance',
                'I53' : 'Thermal transport', 'I54' : 'Thermoelectric effect', 'I55' : 'Spin transport',
                'I56' : 'Other topics', 'I6' : 'Superconductivity', 'I60' : 'Mechanism and paring symmetry',
                'I61' : 'Phenomenology', 'I62' : 'Vortices', 'I63' : 'Tunnel junction and Josephson effect',
                'I64' : 'High-Tc superconductors and related materials', 'I65' : 'Heavy fermion superconductors', 'I66' : 'Organic superconductors',
                'I67' : 'Light-element superconductors', 'I68' : 'Other topics', 'I7' : 'Magnetic and dielectric properties',
                'I70' : 'Magnetic transitions', 'I71' : 'Frustration', 'I72' : 'Kondo effect, heavy fermions',
                'I73' : 'Magnetic resonance', 'I74' : 'Magnetism in nanosystems', 'I75' : 'Spintronics',
                'I76' : 'Dielectric properties', 'I77' : 'Orbital effects', 'I78' : 'Multiferroics',
                'I79' : 'Other topics', 'I8' : 'Optical properties', 'I80' : 'Spectroscopy',
                'I81' : 'Nonlinear optics', 'I82' : 'Exitons and polaritons', 'I83' : 'Photo-induced phase transitions',
                'I84' : 'Ultrafast phenomena', 'I85' : 'Other topics', 'I9' : 'Low dimensional systems -electronic properties',
                'I90' : 'Surfaces, interfaces and thin films', 'I91' : 'Clusters', 'I92' : 'Graphene, fullerene',
                'I93' : 'Nanotube, nanowire', 'I94' : 'Quantum dot', 'I95' : 'Other nanostructures',
                'I96' : 'Quantum Hall effect', 'I97' : 'Other topics', 'J0' : 'Mechanics, elasticity and rheology',
                'J00' : 'Frictions', 'J01' : 'Rheology', 'J02' : 'Linear and nonlinear elasticity',
                'J03' : 'Other mechanical problems', 'J1' : 'Fluid dynamics', 'J10' : 'Complex fluids',
                'J11' : 'Incompressible fluids', 'J12' : 'Compressible fluids and dilute gases', 'J13' : 'Electro-magnetic fluids',
                'J14' : 'Fluids in earth physics and astronomy', 'J15' : 'Convections and turbulences', 'J16' : 'Waves',
                'J17' : 'Creep flows', 'J18' : 'Vortices', 'J19' : 'Other topics in fluid dynamics',
                'J2' : 'Plasma physics', 'J20' : 'Nuclear fusions', 'J21' : 'Plasma astrophysics',
                'J22' : 'Waves, heating, instabilities', 'J23' : 'Transports, confinements', 'J24' : 'Nonlinear phenomena',
                'J25' : 'High energy, high density plasma, strongly coupled systems', 'J26' : 'Electrostatic discharges, ionization, emergence of plasma', 'J27' : 'Magnetic reconnections, particle accelerations, dynamo',
                'J28' : 'Non-neutral plasma, dust plasma', 'J29' : 'Other topics in plasma physics', 'J3' : 'Chemical physics',
                'J30' : 'Chemical reactions', 'J31' : 'Optical response, optical scatterings', 'J32' : 'Solutions and liquids',
                'J33' : 'Quantum chemistry, electronic states', 'J34' : 'Photosynthesis, optical response in biology', 'J35' : 'Supercooled liquids and glasses',
                'J36' : 'Other topics in chemical physics', 'J4' : 'Soft-matter physics', 'J40' : 'Liquid crystals',
                'J41' : 'Polymer physics', 'J42' : 'Gels', 'J43' : 'Glassy systems',
                'J44' : 'Granular physics', 'J45' : 'Other topics in soft-matter physics', 'J5' : 'Biophysics',
                'J50' : 'Proteins, nucleic acids, biomembranes, bio-supramolecules', 'J51' : 'Transmission of information and energy in living bodies', 'J52' : 'Neurons and brains',
                'J53' : 'Biomechanics, physics of biomolecules', 'J54' : 'Immunology', 'J55' : 'Embryology and bio-evolutions',
                'J56' : 'Other topics in biophysics', 'J6' : 'Geophysics', 'J60' : 'Earthquakes',
                'J61' : 'Geofluid mechanics, sand motion', 'J62' : 'Geophysical aspects of planet science', 'J63' : 'Other topics in geophysics',
                'J7' : 'Others', 'J70' : 'Traffic flows and pedestrian dynamics', 'J71' : 'Econophysics, social physics',
                'J72' : 'Physics of games and sports', 'J73' : 'Environmental physics', 'J74' : 'Other topics'}


#urltrunk = "http://%s.oxfordjournals.org/content/%s/%s" % (jnl,vol,issue)
urltrunk = "https://academic.oup.com/%s/issue/%s/%s" % (jnl, vol, issue)

print "get table of content of %s%s.%s via %s ..." %(jnlname, vol, issue, urltrunk)
driver = webdriver.PhantomJS()
driver.get(urltrunk)
#hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
#       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
#       'Accept-Encoding': 'none',
#       'Accept-Language': 'en-US,en;q=0.8',
#       'Connection': 'keep-alive'}
#tocreq = urllib2.Request(urltrunk, headers=hdr)
#tocpage = BeautifulSoup(urllib2.urlopen(tocreq), features="lxml")
tocpage = BeautifulSoup(driver.page_source, features="lxml")




#os.system("lynx -source \"%s.toc\"|grep 'href.* rel=.abstract' > %s/%s.toc" % (urltrunk,tmpdir,jnlfilename))
#f not os.path.isfile(tmpdir+"/"+jnlfilename+".toc"):
 #   os.system("lynx -source \"%s.toc\"|grep href > %s/%s.toc" % (urltrunk,tmpdir,jnlfilename))
#    #include letters
 #   if (jnl == 'mnras') and (issue == 1):
  #      os.system("lynx -source \"%s.toc\"|grep href >> %s/%s.toc" % (re.sub('mnras', 'mnrasl', urltrunk,tmpdir,jnlfilename)))

#print "read table of contents..."
#tocfil = open(tmpdir+"/"+jnlfilename+".toc",'r')
#articleIDs = []

typecode = 'P'
if jnl == 'astrogeo':
    typecode = ''
#typecode = 'C'
note = ''
recnr = 1
recs = []


for div in tocpage.body.find_all('div', attrs = {'class' : 'section-container'}):
    articles = []
    for section in div.find_all('section'):
        for h4 in section.find_all('h4'):
            note = h4.text
        for a in section.find_all('a', attrs = {'class' : 'viewArticleLink'}):
            artlink = "https://academic.oup.com" + a['href']
            articles.append((artlink, note))
    if not articles:
        for a in div.find_all('a', attrs = {'class' : 'viewArticleLink'}):
            artlink = "https://academic.oup.com" + a['href']
            articles.append((artlink, note))
    i = 0 
    for (artlink, note) in articles:
        i += 1
        print '---{ %i/%i }---{ %s }---' % (i, len(articles), artlink)
        try:
            time.sleep(27)
            #pagreq = urllib2.Request(artlink, headers={'User-Agent' : "Magic Browser"})
            #page = BeautifulSoup(urllib2.urlopen(pagreq), features="lxml")
            driver.get(artlink)
            page = BeautifulSoup(driver.page_source, features="lxml")
        except:
            print "retry in 180 seconds"
            time.sleep(180)
            pagreq = urllib2.Request(artlink, headers={'User-Agent' : "Magic Browser"})
            page = BeautifulSoup(urllib2.urlopen(pagreq), features="lxml")
        rec = {'issue' : issue, 'vol' : vol, 'jnl' : jnlname, 'note' : [], 'tc' : typecode,
               'refs' : [], 'autaff' : [], 'keyw' : []}
        #not completely loaded?
        for meta in page.find_all('meta', attrs = {'name' : 'citation_doi'}):
            rec['doi'] = meta['content']
        if 'doi' in rec.keys():
            print '   ', rec['doi']
        else:
            print "retry in 180 seconds"
            time.sleep(180)
            pagreq = urllib2.Request(artlink, headers={'User-Agent' : "Magic Browser"})
            page = BeautifulSoup(urllib2.urlopen(pagreq))                               
        if note:
            rec['note'] = [note]
        for meta in page.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                if meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content']
                elif meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content']
                elif meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                elif 'citation_author' == meta['name']:
                    aut = meta['content']
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
                    if re.search(' Collaboration', aut):
                        rec['col'] = re.sub('^[tT]he ', '', re.sub(' Collaboration', '', aut))
                    else:
                        if re.search(',', aut):
                            rec['autaff'].append([aut])
                        else:
                            rec['autaff'].append([re.sub('(.*) (.*)', r'\2, \1', aut)])
                elif 'citation_author_institution' == meta['name']:
                    if len(rec['autaff']) > 0:
                        rec['autaff'][-1].append(re.sub('^\d*', '', meta['content']))                        
                elif meta['name'] == 'citation_pdf_url':
                    rec['citation_pdf_url'] = meta['content']
                    if jnl == 'ptep':
                        rec['p1'] = re.sub('.*\/20\d\d\/\d+\/(.*?)\/.*', r'\1', rec['citation_pdf_url'])
        for abstract in page.find_all('section', attrs = {'class' : 'abstract'}):
            try:
                fsunwrap(abstract)
                rec['abs'] = re.sub('\n *', ' ', abstract.p.text.strip())
            except:
                print ' -- no abstract --'
        for ref in page.find_all('div', attrs = {'class' : 'ref-content'}):
            refdois = []
            for a in ref.find_all('a'):
                atext = a.text                
                if re.search('Cross[rR]ef', atext) or re.search('https?...doi.org.', atext):
                    refdoi = re.sub('http.*doi.org.', ', DOI: ', a['href']+' ')
                    if not refdoi in refdois:
                        a.replace_with(refdoi)
                        refdois.append(refdoi)
                    else:
                        a.replace_with('')
                elif re.search('Google Scholar', atext) or re.search('PubMed', atext) or re.search('Search ADS', atext):
                    a.replace_with(' ')
            rec['refs'].append([('x', ref.text)])
        #PASJ p1
        if (jnl == 'pasj'): 
            for wwco in page.find_all('div', attrs = {'class' : 'ww-citation-primary'}):
                rec['p1'] = re.sub('.*: (.*?)\.?$', r'\1', wwco.text)
                if re.search('Publications of the Astronomi.*Page', rec['p1']):
                    rec['p1'] = re.sub(',.*', '', re.sub('.*Pages? ', '', rec['p1']))
        elif (jnl == 'nsr'):
            rec['p1'] = re.sub('.*\/', '', rec['doi'])
        #licence
        for a in page.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons', a['href']):
                rec['licence'] = {'url' : a['href']}
                if 'citation_pdf_url' in rec.keys():
                    rec['FFT'] = rec['citation_pdf_url']
        #PASJ keywords
        for a in page.find_all('a', attrs = {'class' : 'kwd-part kwd-main'}):
            rec['keyw'].append(a.text)
        #PTEP keywords
        for am in page.find_all('div', attrs = {'class' : 'article-metadata'}):
            for a in am.find_all('a'):
                if a.has_attr('href') and re.search('PTEP', a['href']):
                    rec['keyw'].append(a.text)
        print '   ', rec.keys()
        recs.append(rec)



#    for ul in page.body.find_all('ul'):
#        if ul.attrs.has_key('class') and "kwd-group" in ul['class']:
#            rec['keyw'] = []
#            for kli in ul.find_all('li'):
#                for a in kli.find_all('a'):
#                    if jnl == 'ptep' and ptepcollcode.has_key(a.string):
#                        rec['keyw'].append(ptepcollcode[a.string])
#                    else:
#                        rec['keyw'].append(a.string)
 




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
