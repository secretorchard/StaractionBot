# library config
import pywikibot as pwb
from datetime import date
import urllib.request as rq
import json
import us

accessdate = date.today().strftime("%B %d, %Y") # timestamp

def search(title, state, id):
    stateabbr = us.states.lookup(state).abbr.lower() # convert state name to abbreviation
    filteredtitle = title.replace(" ", "_")
    with rq.urlopen(f'https://dashboard.waterdata.usgs.gov/service/geocoder/get/location/1.0?term={filteredtitle}&include=gnis,state&states={stateabbr}') as url:
        data = json.loads(url.read().decode())
    if (data[0]['GnisId'] == id and data[0]['Name'] == title): return True
    else: return False

def main():
    # pwb config
    pagetitle = 'Wild Meadow, West Virginia'
    site = pwb.Site('en', 'wikipedia') # running on enwiki
    page = pwb.Page(site, pagetitle) # page to run on

    # replacement string processing
    TRreading = open("toreplace.txt") # this contains everything within the ref tag; ie. {{cite web|url=http://geonames.usgs.gov|accessdate=2008-01-31|title=US Board on Geographic Names|publisher=[[United States Geological Survey]]|date=2007-10-25}}
    toreplace = TRreading.read() # TODO: instead of replacing a fixed thing, replace everything within <ref name="GR3"></ref>
    
    # finding gnis id on page
    rwktxt = page.text
    rawgnisid = rwktxt[rwktxt.rfind(" ", 0, rwktxt.find(f'<ref name="GR3">'))+1:rwktxt.find(f'<ref name="GR3">')] # splice out the part right after a space and before the <ref> tag

    # dummy variables for now
    gnisid = int(rawgnisid)
    gnisstate = pagetitle[pagetitle.rfind(', ') + 2:]
    gnistitle = pagetitle[:pagetitle.find(',')]

    if (search(gnistitle, gnisstate, gnisid) == False): print(gnisid) # TODO: put misfits in a page in bot userspace
    else:
        # replacement onwiki
        tr = page.text.replace(toreplace, f'<ref name="GR3">{{{{cite gnis|{gnisid}|{gnistitle}|{accessdate}}}}}</ref>')
        editsummary = f'replacing dead citation with {{{{cite gnis}}}}'
        page.put(tr, summary=editsummary, minor=False)

# boilerplate
if __name__ == "__main__":
    main()