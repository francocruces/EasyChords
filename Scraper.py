import requests
import requests.adapters
from bs4 import BeautifulSoup
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, \
    InlineKeyboardMarkup

from Config import NO_RESULTS_ALERT, CANCEL_DATA_STRING, NO_RESULTS_TEXT, CANCEL_BUTTON_TEXT, \
    TITLE_ARTIST_SEPARATOR, REFINE_BUTTON_TEXT, MAX_BUTTON_DATA, MAX_RESULTS

__author__ = "Franco Cruces Ayala"


def get_chords_as_inline_keyboard(query):
    """
    Return a InlineQueryResultArticle object. The selection sends a message with an inline keyboard, where every button
    is a search result.
    :param query: A query for searching @https://www.ultimate-guitar.com/
    :return: an InlineQueryResultArticle object
    """
    buttons = get_inline_keyboard_buttons(query)
    if len(buttons) > 0:
        buttons.append([InlineKeyboardButton(
            text=REFINE_BUTTON_TEXT,
            switch_inline_query_current_chat=query
        )])
        buttons.append([InlineKeyboardButton(
            text=CANCEL_BUTTON_TEXT,
            callback_data=CANCEL_DATA_STRING,
        )])
        return [InlineQueryResultArticle(
            id=query,
            title="Search for " + query,
            description=str(len(buttons)) + " results found",
            input_message_content=InputTextMessageContent(message_text='Results for "*' + query + '*".\n' + str(
                len(buttons)) + ' results found.\n' + '_Choose a result to load._',
                                                          parse_mode="Markdown"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )]
    else:
        return [InlineQueryResultArticle(
            id=0, title=NO_RESULTS_TEXT, input_message_content=InputTextMessageContent(
                message_text=NO_RESULTS_ALERT,
                parse_mode="Markdown")
        )]


def get_inline_keyboard_buttons(query):
    """
    Get chords from UG. First search and then generate Articles as a Inline Query Result.
    :param query: A query for searching @https://www.ultimate-guitar.com/
    :return: Array with InlineKeyboardButtons
    """
    buttons = []
    search_results = get_search_result(query)
    count = 0
    for song in search_results:
        title = song['title'] + TITLE_ARTIST_SEPARATOR + song['artist']
        if len(song['url'].replace('https://tabs.ultimate-guitar.com/', '')) > MAX_BUTTON_DATA:
            continue
        buttons.append([InlineKeyboardButton(
            text=title,
            callback_data=song['url'].replace('https://tabs.ultimate-guitar.com/', ''),
        )])
        count += 1
        if count >= MAX_RESULTS:
            break
    return buttons


def get_chords(url_suf):
    """
    Get chords from given url
    :param url_suf: UG URL suffix
    :return: chord section for given URL as a string
    """
    print("Requesting: " + 'https://tabs.ultimate-guitar.com/' + url_suf)
    page = requests.get(
        'https://tabs.ultimate-guitar.com/' + url_suf)
    soup = BeautifulSoup(page.content, 'lxml')
    chords = soup.find_all("pre", class_='js-tab-content js-init-edit-form js-copy-content js-tab-controls-item')[
        0].text
    return chords


def get_search_result(query):
    """
    Search given query at https://www.ultimate-guitar.com/s. Return array of songs where each element is a dictionary
    :param query: A query for searching @https://www.ultimate-guitar.com/search.php
    :return: Array with dictionaries
    """
    search_query = "https://www.ultimate-guitar.com/search.php?title=" \
                   + query.replace(" ", "+") + "&page=1&tab_type_group=text&app_name=ugt&order=myweight&type=300"
    print("Search: " + search_query)
    page = requests.get(search_query)
    soup = BeautifulSoup(page.content, 'lxml')
    if not soup.find_all("table", class_='tresults'):
        return []
    rows = soup.find_all("table", class_='tresults')[0].find_all('tr')
    results = []
    count = 0
    for a_row in rows:
        row = a_row.find_all('td')
        if not len(row):
            continue
        off = 0
        if row[0].text == "THIS APP DOESN'T HAVE RIGHTS TO DISPLAY TABS":
            off = 1
        search_result = {
            'artist': row[0 + off].text.strip(),
            'url': row[1 + off].a.get('href'),
            'title': row[1 + off].text.replace("\n", "").split("+")[0].split(" info ")[0].strip(),
            'rating': row[2 + off].span.get("title") if not (row[2].span is None) else "No Rating",
            'amount_ratings': row[2 + off].find_all('b', class_="ratdig")[0].text if len(
                row[2].find_all('b', class_="ratdig")) != 0 else "-",
            'rtype': row[3 + off].text.replace("\n", "")}
        results.append(search_result)
        count += 1
    return filter_type(fix_artists(results), "chords")


def fix_artists(array):
    curr_artist = ""
    for r in array:
        if r['artist'] != "":
            curr_artist = r['artist']
        r['artist'] = curr_artist
    return array


def filter_type(array, type_string):
    new_array = []
    for r in array:
        if r['rtype'] == type_string:
            new_array.append(r)
    return new_array
