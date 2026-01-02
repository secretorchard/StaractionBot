# library config
import pywikibot as pwb
from datetime import datetime, timezone
import urllib.request as rq
import json
import us

accessdate = datetime.now(timezone.utc).strftime("%Y-%m-%d") # timestamp

def search(title, state, id):
    stateabbr = us.states.lookup(state).abbr.lower() # convert state name to abbreviation
    filteredtitle = title.replace(" ", "_")
    with rq.urlopen(f'https://dashboard.waterdata.usgs.gov/service/geocoder/get/location/1.0?term={filteredtitle}&include=gnis,state&states={stateabbr}') as url:
        data = json.loads(url.read().decode())
    if (data[0]['GnisId'] == id and data[0]['Name'] == title): return True
    else: return False

def findgnisid(page):
    # finding gnis id on page
    rwktxt = page.text
    try:
        rawgnisid = rwktxt[rwktxt.rfind(" ", 0, rwktxt.find(f'<ref name="GR3">')) + 1:rwktxt.find(f'<ref name="GR3">')] # splice out the part right after a space and before the <ref> tag
        gnisid = int(rawgnisid) # gnis id, as on the Wikipedia page
        return gnisid
    except:
        return False

def main(ptitle):   
    # pwb config 
    site = pwb.Site('en', 'wikipedia') # running on enwiki
    page = pwb.Page(site, pagetitle) # page to run on

    # finding gnis id on page
    rwktxt = page.text
    rawgnisid = rwktxt[rwktxt.rfind(" ", 0, rwktxt.find(f'<ref name="GR3">')) + 1:rwktxt.find(f'<ref name="GR3">')] # splice out the part right after a space and before the <ref> tag

    # replacement string processing
    toreplace = rwktxt[rwktxt.find(f'<ref name="GR3">'):rwktxt.find("</ref>", rwktxt.find(f'<ref name="GR3">')) + 6] # TODO: replace the +6 with detection of digits instead

    gnisid = findgnisid(page) # finding gnis id on page

    gnisstate = pagetitle[pagetitle.rfind(', ') + 2:] # takes state name from page title
    gnistitle = pagetitle[:pagetitle.find(',')] # takes location name from page title

    if (search(gnistitle, gnisstate, gnisid) == False): 
        lpage = pwb.Page(site, 'User:StaractionBot/Tasks/1/logged')
        ltxt = lpage.text
        if (gnisid == False): lpage.put(ltxt + "\n* " + "[[" + pagetitle + "]]" +  ", " + "given ID = failed to get", summary = "logging failed citation replacement on " + "[[" + pagetitle + "]] ([[User:StaractionBot/Tasks/1.1|task 1.1]])")
        else: lpage.put(ltxt + "\n* " + "[[" + pagetitle + "]]" +  ", " + "given ID = " + str(gnisid), summary = "logging failed citation replacement on " + "[[" + pagetitle + "]] ([[User:StaractionBot/Tasks/1.1|task 1.1]])")
    else:
        # replacement onwiki
        tr = page.text.replace(toreplace, f'<ref name="GR3-u">{{{{cite gnis|{gnisid}|{gnistitle}|{accessdate}}}}}</ref>')
        editsummary = f'replacing generic citation with {{{{cite gnis}}}} ([[User:StaractionBot/Tasks/1|task 1]])'
        page.put(tr, summary=editsummary, minor=False)

# boilerplate
if __name__ == "__main__":
    with open('toreplace.txt') as file: 
        for pagetitle in file: 
            print(pagetitle)
            main(pagetitle)