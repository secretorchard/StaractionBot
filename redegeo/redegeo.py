# library config
import pywikibot as pwb
from datetime import datetime, timezone
import urllib.request as rq
import json
import us

accessdate = datetime.now(timezone.utc).strftime("%Y-%m-%d") # timestamp

def search(title, state, id):
    filteredtitle = title.replace(" ", "_").replace("&", "and").replace("St.", "Saint")
    if (state != None):
        try:
            stateabbr = us.states.lookup(state).abbr.lower() # convert state name to abbreviation 
        except:
            return False
        with rq.urlopen(f'https://dashboard.waterdata.usgs.gov/service/geocoder/get/location/1.0?term={filteredtitle}&include=gnis&states={stateabbr}') as url:
            data = json.loads(url.read().decode())
    else:
        with rq.urlopen(f'https://dashboard.waterdata.usgs.gov/service/geocoder/get/location/1.0?term={filteredtitle}&include=gnis') as url:
            data = json.loads(url.read().decode())
    for datum in data:
        if len(data) == 1:
            if (str(datum['GnisId']) == id) and (str(datum['Name']) == str(title)): return True # issue with leading zeros in ints
        elif str(datum['Type']) == "Cities & Populated Places":
            if (str(datum['GnisId']) == id) and (str(datum['Name']) == str(title)): return True
    return False

# finding gnis id on page
def findgnisid(page):
    try:
        try:
            # wikidata config (preferred)
            wikidataitem = pwb.ItemPage.fromPage(page)
            item_dict = wikidataitem.get()
            claims = item_dict["claims"]
            if len(claims["P590"]) == 1: 
                for claim in claims["P590"]: gnisid = claim.getTarget()
            else: 
                for claim in claims["P590"]:
                    if claim.has_qualifier("P2868", "Q486972"): gnisid = claim.getTarget()
            return str(gnisid)
        except:
            # wikipedia page config (backup)
            rwktxt = page.text
            gnisid = rwktxt[rwktxt.rfind(" ", 0, rwktxt.find(f'<ref name="GR3">')) + 1:rwktxt.find(f'<ref name="GR3">')] # splice out the part right after a space and before the <ref> tag
            return str(gnisid)
    except:
        return False

def main(ptitle):   
    # pwb config 
    site = pwb.Site('en', 'wikipedia') # running on enwiki
    page = pwb.Page(site, pagetitle) # page to run on

    # finding gnis id on page
    rwktxt = page.text

    # replacement string processing
    toreplace = rwktxt[rwktxt.find(f'<ref name="GR3">'):rwktxt.find("</ref>", rwktxt.find(f'<ref name="GR3">')) + 6] # TODO: replace the +6 with detection of digits instead

    gnisid = findgnisid(page)

    try:
        wikidataitem = pwb.ItemPage.fromPage(page)
        gnistitle = wikidataitem.labels['en'].strip() # takes location name from Wikidata item (preferred)
    except:
        gnistitle = ptitle[:ptitle.find(',')].strip() # takes location name from page title (backup backup)

    try:
        gnisstate = ptitle[ptitle.rfind(', ') + 2:].strip() # takes state name from page title (backup)
    except:
        gnisstate = None

    # GNIS lists townships as "Township of [x]" instead of "[x] Township"
    if "Township" in gnistitle:
        gnistitle = "Township of " + gnistitle[:gnistitle.find('Township')].strip()

    if (search(gnistitle, gnisstate, gnisid) == False): 
        lpage = pwb.Page(site, 'User:StaractionBot/Tasks/1/logged')
        ltxt = lpage.text
        if (gnisid == False): lpage.put(ltxt + "\n* " + "[[" + ptitle + "]]" +  ", " + "given ID = failed to get", summary = "logging failed citation replacement on " + "[[" + pagetitle + "]] ([[User:StaractionBot/Tasks/1.1|task 1.1]])")
        else: lpage.put(ltxt + "\n* " + "[[" + ptitle + "]]" +  ", " + "given ID = " + str(gnisid), summary = "logging failed citation replacement on " + "[[" + pagetitle + "]] ([[User:StaractionBot/Tasks/1.1|task 1.1]])")
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