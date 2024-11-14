import datetime
import json
import os
import requests
import concurrent.futures
from types import SimpleNamespace
from pathvalidate import sanitize_filename
import xml.etree.cElementTree as ET


# CHANGE THIS TO PULL CARD ARTWORKS FROM OFFICIAL WEBSITE
DL_ARTWORK = False

# CHANGE THIS TO DETERMINE HOW MANY THREADS TO CREATE FOR ADDING CARDS / DOWNLOADING ART
DL_THREADS = 4


XmlRoot = ET.Element("cockatrice_carddatabase", version="4")
XmlInfo = ET.SubElement(XmlRoot, "info")
XmlSets = ET.SubElement(XmlRoot, "sets")
XmlCards = ET.SubElement(XmlRoot, "cards")


def openJson(filename):
    with open(filename, 'r', encoding="utf-8") as file:
        data = json.load(file)
    
    return data


def initCockTree():
    ET.SubElement(XmlInfo, "author").text = "MrDetonia"
    ET.SubElement(XmlInfo, "createdAt").text = str(datetime.datetime.now())
    ET.SubElement(XmlInfo, "sourceUrl").text = "https://github.com/CCondeluci/WeissSchwarz-ENG-DB"
    ET.SubElement(XmlInfo, "sourceVersion").text = "TESTING"


def addSet(name, expansion):
    xmlSet = ET.SubElement(XmlSets, "set")
    ET.SubElement(xmlSet, "name").text = name
    ET.SubElement(xmlSet, "longname").text = expansion
    ET.SubElement(xmlSet, "settype").text = "Weiss:Schwarz"


def addCard(card):
    print(f"Adding card: {card['name']}")
    # map card attributes to XML
    xmlCard = ET.SubElement(XmlCards, "card")
    ET.SubElement(xmlCard, "name").text = sanitize_filename(card["name"])

    # build description
    abilities = ""
    for ability in card['ability']:
        abilities = f"{abilities}\n{ability}"

    descr = f"\
Colour: {card['color']} | Level: {card['level']} / Cost: {card['cost']}\n\n\
{card['flavor_text']}\n\n\
{abilities}\n\n\
Power: {card['power']}"

    ET.SubElement(xmlCard, "text").text = descr

    xmlProp = ET.SubElement(xmlCard, "prop")
    ET.SubElement(xmlProp, "side").text = "front"
    ET.SubElement(xmlProp, "layout").text = "normal"
    ET.SubElement(xmlProp, "type").text = card["type"]
    ET.SubElement(xmlProp, "maintype").text = card["type"]

    ET.SubElement(xmlCard, "set").text = f"{card['set']}/{card['release']}"

    # download card artwork (optional)
    if DL_ARTWORK:
        target = f"./export/pics/{sanitize_filename(card['name'])}.png"
        if not os.path.isfile(target):
            print(f"Downloading: {target}")
            imgData = requests.get(card["image"]).content

            with open(target, "wb") as file:
                file.write(imgData)
        else:
            print(f"Skipping {target} - file exists.")


def addCards(filename):
    json = openJson(filename)

    # identify and add set
    print(f"Adding cards from: {json[0]['expansion']}")
    if DL_ARTWORK:
        print("WARNING: downloading card artworks! This could take some time.")

    addSet(f"{json[0]['set']}/{json[0]['release']}", json[0]["expansion"])

    # add all cards
    with concurrent.futures.ThreadPoolExecutor(max_workers=DL_THREADS) as executor:
        executor.map(addCard, json)

    print(f"Done adding cards from: {json[0]['expansion']}")


def main():
    # setup
    initCockTree()

    # import all sets from directory
    directory = "./WeissSchwarz-ENG-DB/DB"

    for filename in os.listdir(directory):
        file = os.path.join(directory, filename)
        if os.path.isfile(file):
            addCards(file)

    # export XML
    xmlTree = ET.ElementTree(XmlRoot)
    ET.indent(xmlTree, space="  ", level=0)
    xmlTree.write("./export/WeissSchwarz.xml", encoding="utf-8")
    print("Done! Cockatrice set available in ./export")


if __name__ == "__main__":
    main()