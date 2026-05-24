# library config
import pywikibot as pwb
import urllib.request as rq
import mwparserfromhell
from pywikibot.exceptions import InvalidTitleError

# pwb config
site = pwb.Site("en", "wikipedia") # running on enwiki

#def main():
page = pwb.Page(site, "Wikipedia:Arbitration enforcement log/Protections") # log page
lines = page.text.splitlines()

# logging
logPage = pwb.Page(site, "User:StaractionBot/Tasks/3.1/log")

def log(toLog, s):
    logText = logPage.text
    logPage.put(logText + "\n* " + toLog, summary = s + " ([[User:StaractionBot/Tasks/3.1|task 3.1]])")

# read whitelist
whitelist = pwb.Page(site, "User:StaractionBot/Tasks/3.1/whitelist") # whitelist page
whitelistLines = whitelist.text.splitlines()

# trial counter
counter = 0

for line in reversed(lines): 
    if (counter >= 47):
        print("hit 50 edits!")
        break

    if (("{User:ClerkBot/AE entry" in line) and ("[edit=extendedconfirmed] (indefinite)" in line)):
        # find page
        textstart = line.index("|page=") # start of page text
        textend = line.index("|date=") # end of page text
        articleTitle = line[textstart + 6:textend] # article title

        # find log entry
        logstart = line.index("|logid=") # start of logid
        logend = line.index("|admin=") # end of logid
        logEntry = line[logstart + 7:logend] # log entry

        # editnotice page
        oldTemplateNoticePage = pwb.Page(site, "Template:Editnotices/Page/" + articleTitle) # editnotice template page

        # set as Page object
        p = pwb.Page(site, articleTitle)

        # some cases to be careful of: if a redirect, set to the page being redirected to
        if (p.isRedirectPage() == 1): p = p.getRedirectTarget() 

        # define editnotice template page for redirect target
        templateNoticePage = pwb.Page(site, "Template:Editnotices/Page/" + p.title()) 

        # talk page & category
        talkPage = pwb.Page(site, "Talk:" + p.title())
        talkCat = pwb.Category(site, "Category:Wikipedia pages subject to the extended confirmed restriction related to the Arab-Israeli conflict")
        talkCatBroad = pwb.Category(site, "Category:Wikipedia pages about contentious topics")

        # check if in whitelist
        if ((("* " + articleTitle) in whitelistLines) or (("* " + p.title()) in whitelistLines)):
            print(p.title() + " or " + articleTitle + " in whitelist, skipping...")

        else:
            # we only want PIA articles for now
            if ("|topic=a-i}" in line):

                if (templateNoticePage.exists() == 0):

                    # some cases to be careful of: we want only mainspace pages, and pages that currently exist
                    if (p.exists() != 0 and p.namespace() == 0 and p.isDisambig() != 1): # if page exists & is in mainspace & isn't a disambiguation page

                        # we do not want redirects to a particular section of the page
                        if ("#" not in p.title()):

                            # detecting whether the page is still protected
                            if (p.protection().get("edit") == ("extendedconfirmed", "infinity")): 

                                # see if previous page had an editnotice
                                if (oldTemplateNoticePage.exists() == 1): 
                                    log("[[" + articleTitle + "]] page redirects to section on [[" + p.title() + "]] with existing redirect editnotice. Consider move?", "logging editnotice status of [[" + articleTitle + "]]")
                                
                                else:
                                    # create editnotice
                                    print("Adding editnotice to page " + articleTitle)
                                    templateNoticePage.put("{{Contentious topics/editnotice|topic=a-i}}", summary = "Creating [[WP:CT/PIA]] editnotice per [[Special:Redirect/logid/" + logEntry + "|page protection]] ([[User:StaractionBot/Tasks/3.1|task 3.1]])") 
                                    counter = counter + 1

                            else:
                                # log, as non-protected but in protection log (perhaps expiring?)
                                log("Non-protected but in protection log on [[" + articleTitle + "]]", "logging editnotice status of [[" + articleTitle + "]]")
                                flag = 4

                        else:

                            if (p.protection().get("edit") == ("extendedconfirmed", "infinity")): 

                                # log, as page redirect to section
                                if (templateNoticePage.exists() == 0):

                                    if (oldTemplateNoticePage.exists() == 1):
                                        log(oldP + " page redirects to section on [[" + p.title() + "]] with existing redirect editnotice. Consider move?", "logging editnotice status of [[" + articleTitle + "]]")

                                else:

                                    if (oldTemplateNoticePage.exists() == 1):
                                        log(oldP + " redirects to [[" + p.title() + "]]; both have editnotices. Consider deletion?", "logging editnotice status of [[" + articleTitle + "]]")

                                # nothing to fix

                    else:
                        # skip, as non-mainspace or non-existent page
                        flag = 2 # dummy

                else:
                    # skip, as already has editnotice
                    flag = 10

                # talk page notices

                if (talkCat not in talkPage.categories() and talkCatBroad not in talkPage.categories()):

                    # detecting whether the page is still protected & want only mainspace pages, and pages that currently exist
                    if (p.protection().get("edit") == ("extendedconfirmed", "infinity") and p.exists() != 0 and p.namespace() == 0 and p.isDisambig() != 1): 
                        # add talk template to talk page, spaghetti code follows
                        print("Adding talk notice to " + talkPage.title())
                        wikicode = mwparserfromhell.parse(talkPage.text)
                        sections = wikicode.get_sections(include_lead=True)
                        header = sections[0]
                        wikicode_headersonly = mwparserfromhell.parse(header)
                        importantFlag = 0

                        for template in reversed(wikicode_headersonly.filter_templates()):
                            template_name = str(template.name).strip()
                            template_page = pwb.Page(site, "Template:" + template_name)

                            if template_page.isRedirectPage():
                                template_name = template_page.getRedirectTarget().title(with_ns=0)

                            if (template_name.lower() == "talk header"): # talk header then skip then nom
                                wikicode.insert_after(template, "\n{{contentious topics/talk notice|topic=a-i}}")
                                talkPage.put(wikicode, summary = "Adding [[WP:CT/PIA]] talk notice per [[Special:Redirect/logid/" + logEntry + "|page protection]] ([[User:StaractionBot/Tasks/3.1|task 3.1]])")
                                importantFlag = 1
                                break
                            elif (template_name.lower() == "skip to talk") or (template_name.lower() == "top of page") or (template_name.lower() == "skip to section") or (template_name.lower() == "back to contents") or (template_name.lower() == "skip to top") or (template_name.lower() == "skip to bottom"):
                                wikicode.insert_after(template, "\n{{contentious topics/talk notice|topic=a-i}}")
                                talkPage.put(wikicode, summary = "Adding [[WP:CT/PIA]] talk notice per [[Special:Redirect/logid/" + logEntry + "|page protection]] ([[User:StaractionBot/Tasks/3.1|task 3.1]])")
                                importantFlag = 2
                                break
                            elif (template_name.lower() == "ga nominee") or (template_name.lower() == "peer review") or (template_name.lower() == "featured article candidates") or (template_name.lower() == "featured list candidates"):
                                wikicode.insert_after(template, "\n{{contentious topics/talk notice|topic=a-i}}")
                                talkPage.put(wikicode, summary = "Adding [[WP:CT/PIA]] talk notice per [[Special:Redirect/logid/" + logEntry + "|page protection]] ([[User:StaractionBot/Tasks/3.1|task 3.1]])")  
                                importantFlag = 3
                                break
                            else:
                                importantFlag = 0

                        if (importantFlag == 0):
                            talkPage.put("{{contentious topics/talk notice|topic=a-i}}\n" + talkPage.text, summary = "Adding [[WP:CT/PIA]] talk notice per [[Special:Redirect/logid/" + logEntry + "|page protection]] ([[User:StaractionBot/Tasks/3.1|task 3.1]])")

                        counter = counter + 1

                else:
                    # skip, as already has talk page template
                    flag = 19

            else: 
                # skip, as non-ARBPIA
                flag = 1 # dummy

    else: 
        # skip, as this particular line isn't a protected page
        flag = 0 # dummy