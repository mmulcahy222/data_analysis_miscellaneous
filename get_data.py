# %%
from helpers import *
from bs4 import BeautifulSoup
import mwparserfromhell
import json
import os
import re
import pprint
from urllib.parse import urlencode, quote, quote_plus
import csv


# GET THE WIKIPEDIA FILE OR SAVE PAGE
def get_wikipedia_json_by_player_name(player_name):
    player_name = player_name.replace(" ", "_")
    json_directory = 'redacted/data_analysis/nba/json/'
    json_full_path = json_directory + f'{player_name}.json'
    # Unicode for Europeans
    if player_name.isascii() is False:
        player_name = quote(player_name)
    # If Exists
    if(os.path.exists(json_full_path)):
        print(f'LOCAL FILE SYSTEM> Retrieving contents from {json_full_path}')
        return json.loads(file_get_contents(json_full_path))
    url = f'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles={player_name}&rvslots=*&rvprop=content&formatversion=2&format=json'
    response = get_html(url)
    # contingencies
    if re.search("may refer to:", response) is not None:
        new_query = player_name + "_(basketball)"
        response = get_html(
            f'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles={new_query}&rvslots=*&rvprop=content&formatversion=2&format=json')
    if re.search("#REDIRECT", response) is not None:
        new_query = re.findall("\[\[(.*)\]\]", response)[0]
        new_query = new_query.replace(" ", "_")
        response = get_html(
            f'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles={new_query}&rvslots=*&rvprop=content&formatversion=2&format=json')
    bytes_written = file_put_contents(json_full_path, response)
    print(f'{bytes_written} for {player_name}')
    return response


# get the JSON from the player list file by calling the function get_wikipedia_json_by_player_name
def get_all_json():
    # list gathered by clean_draft.ipynb
    with open("players_list.txt", "r", encoding="utf8") as f:
        players_list = eval(f.read())
    for i, player_name in enumerate(players_list):
        print(f"{i}")
        get_wikipedia_json_by_player_name(player_name)

# %%
def n_a(f):
  def wrapper(*args, **kwargs):
    try:
        return f(*args, **kwargs)
    except:
        return "N/A"
  return wrapper

class PlayerArticle():
    def __init__(self, player_name):
        # Parameter: Unformatted Player Name
        #
        # Parses the json file into
        #
        # START -- Change File Name to format recognizable in file system
        self.unformatted_player_name = player_name
        player_name = player_name.replace(" ", "_")
        json_directory = 'redacted/data_analysis/nba/json/'
        json_full_file_path = json_directory + f'{player_name}.json'
        # END -- changing player name recognizable to the file system
        json_wikipedia = json.loads(file_get_contents(json_full_file_path))
        content = json_wikipedia.get("query", {}).get("pages", [])[0].get(
            "revisions", [])[0].get("slots", {}).get("main", {}).get("content", {})
        self.parsed_wiki = mwparserfromhell.parse(content)
        # START - initialize infobox
        templates = self.parsed_wiki.filter_templates()
        infobox = None
        for template in templates:
            if template.name.contains('Infobox') is True:
                infobox = template
                break
        self.infobox = infobox
        # END - initialize infobox
    def get_infobox_value(self,infobox_value):
        return self.infobox.get(infobox_value).split("=")[-1].replace("\n","").strip()
    @property
    @n_a
    def draft_year(self):
        return self.get_infobox_value("draft_year")
    @property
    @n_a
    def draft_pick_overall(self):
        try:
            draft_pick = self.get_infobox_value("draft_pick")
        except ValueError:
            #undrafted
            draft_pick = '61'
        return draft_pick 
    @property
    @n_a
    def career_years(self):
        templates = self.parsed_wiki.filter_templates()
        t = templates[0]
        career_years = 0
        for template in templates:
            if template.name.matches('nbay') is True:
                nbay_params = template.params
                if len(nbay_params) == 1:
                    career_years += 1
        return str(career_years)
    def csv_row(self):
        return [self.unformatted_player_name,self.career_years,self.draft_year,self.draft_pick_overall]
#%%
csv_file_name = "player_nba_extra_information.csv"
with open("players_list.txt", "r", encoding="utf8") as f:
    players_list = eval(f.read())
for player_name in players_list[:]:
    with open(csv_file_name, 'a', encoding='utf-8',newline='') as csvfile:
        try:
            player_article = PlayerArticle(player_name)
        except IndexError:
            continue
        print(player_article.csv_row())
        fieldnames = ['player_name', 'career_years','draft_year','draft_pick_overall']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(dict(zip(fieldnames,player_article.csv_row())))
# %%
