import json,glob,os,re,collections
KW={
 'cos':r'cosmolog|dark matter|dark energy|\bcmb\b|microwave background|large[- ]scale structure|lensing|inflation|21[- ]cm|reionization|\bbao\b',
 'exo':r'exoplanet|planet|habitab|astrobiolog|brown dwarf',
 'xgal':r'galax|\bagn\b|active galactic|quasar|galaxy cluster|clusters of galaxies|high[- ]redshift|extragalactic|cosmic noon',
 'galac':r'milky way|galactic structure|\bgaia\b|stellar stream|galactic astronomy|globular|galactic archaeology',
 'he':r'x-ray|gamma[- ]ray|black hole|neutron star|pulsar|compact object|high[- ]energy astro|transient|gravitational[- ]wave|multi-?messenger|\bligo\b|\blisa\b|kilonova|supernova|\bgrb\b|accretion|time[- ]domain',
 'star':r'stellar|\bstars?\b|\bsun\b|solar|helio|asteroseism|binary star|binaries|white dwarf',
 'ism':r'star formation|interstellar|\bism\b|molecular cloud|astrochem|protostell|protoplanetary',
 'inst':r'instrument (?:science|scientist|development|builder)|instrumentation (?:development|postdoc|fellowship)|detector|adaptive optics|telescope technolog|spectrograph|coronagraph design|integrated photonics|cryogenic|interferomet\w* (?:sensor|prototype)',
}
EXCL={'yale-mossman-postdoctoral-fellowship-physics','yale-physics-graduate-honors-d-allan-bromley-graduate-fellow'}
def classify(r):
    t=' '.join([r.get('n',''),r.get('e',''),r.get('f','')]).lower()
    s=[k for k,p in KW.items() if re.search(p,t)]
    f=set(r.get('fields',[]))
    if 'grav' in f and 'he' not in s: s.append('he')
    # Instrumentation = building instruments, detectors and telescope technology. Observing time and
    # data-analysis programs are not instrumentation, and fellowships that merely welcome
    # "theory, observation or instrumentation" are open to every area (no asub).
    return s
def eligible(i,r):
    if i in EXCL: return False
    st=set(r.get('stages',[]))&{'tt','ten','pd','gr','ug'}
    if not st: return False
    f=set(r.get('fields',[])); aud=r.get('aud')
    if not (f&{'astro','grav'} or 'all' in f): return False
    if isinstance(aud,list) and aud==['ap']: return False
    if r.get('region')=='Canada' and not st&{'tt','ten','pd'}: return False
    return True
if __name__=='__main__':
    rows={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob('db4/programs/*.json')}
    c=collections.Counter(); n=0; gen=0
    for i,r in rows.items():
        if not eligible(i,r): continue
        n+=1; s=classify(r) if set(r.get('fields',[]))&{'astro','grav'} else []
        if not s: gen+=1
        c.update(s)
    print(n,'eligible; general/all-areas',gen); print(c)
