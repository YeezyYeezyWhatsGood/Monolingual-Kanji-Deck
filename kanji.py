from urllib.request import urlopen
import requests
import csv
from bs4 import BeautifulSoup
import genanki

# set up anki stuff

kanji_model = genanki.Model(
    2006737459,
    '漢字カードタイプ',
    fields = [
        {'name':'漢字'},
        {'name':'頻度'},
        {'name':'音読み'},
        {'name':'訓読み'},
        {'name':'表面意味'},
        {'name':'裏面意味'},
        {'name':'成り立ち'},
        {'name':'手本'},
        {'name':'漢検級'},
    ],
    templates = [
        {
            'name':'Card 1',
            'qfmt' : '{{音読み}}&nbsp;&nbsp;&nbsp;&nbsp;{{訓読み}}<br>{{表面意味}}',
            'afmt' : '{{音読み}}&nbsp;&nbsp;&nbsp;&nbsp;{{訓読み}}<br>{{裏面意味}}<br>{{手本}}<br>{{成り立ち}}',
        },
    ], css='.card { font-family: "ヒラギノ角ゴ Pro W3","Hiragino Kaku Gothic Pro","メイリオ",Meiryo,"ＭＳ Ｐゴシック",sans-serif;font-size: 35px;text-align: center;}')

kanji_deck = genanki.Deck(1331687276, '漢字')



# Generate kanji frequency dictionary

kanji_list_url = "http://vtrm.net/assets/aozora-kanji-frequency.txt"
page = urlopen(kanji_list_url)
html_bytes = page.read()
html = html_bytes.decode("utf-8")
start_index = html.find("一")-2
kanji_freq = {}

for line in html[start_index:].splitlines():
    frequency, kanji = int(line.split("\t")[0]), line.split("\t")[1]
    kanji_freq[frequency] = kanji
# loopy loopy
for i in range(1,7272):
    result = [kanji_freq[i], str(i), '', '', '', '', '', '', '']
    kanjijiten_url = 'https://kanji.jitenon.jp/cat/search_ie.php'
    data = {'how': '漢字', 'getdata':kanji_freq[i], 'search':'match'}
    resp = requests.get(kanjijiten_url, data)
    soup = BeautifulSoup(resp.text, features="html.parser")
    table = soup.find("table", {"class": "kanjirighttb"})
    if table is None:
        continue
    table_body = table.find("tbody")
    rows = table_body.find_all('tr')
    onyomi = ''
    kunyomi = ''
    imi = ''
    cat = ''
    for row in rows:
        th = row.find('th')
        if th is not None:
            cat = th.text
        if cat == '音読み':
            onyomi = onyomi + ' ' + row.find('td').text
        if cat == '訓読み':
            kunyomi = kunyomi + ' ' + row.find('td').text
        if cat == '意味':
            imi = imi + ' ' + row.find('td').text
    onyomi = onyomi.replace("△", "[△]")
    onyomi = onyomi.replace("小", "[小]")
    onyomi = onyomi.replace("中", "[中]")
    onyomi = onyomi.replace("高", "[高]")
    kunyomi = kunyomi.replace("小", "[小]")
    kunyomi = kunyomi.replace("中", "[中]")
    kunyomi = kunyomi.replace("高", "[高]")
    kunyomi = kunyomi.replace("△", "[△]")
    imi = imi.replace("日本","[日本]")
    result[2] = onyomi
    result[3] = kunyomi
    result[4] = imi.replace(kanji_freq[i], '◯')
    result[5] = imi

    # get the kanken level
    kanken = soup.find(string='漢検級')
    if kanken is not None:
        result[8] =  kanken.next_element.text
    else:
        result[8] = '?'

    url = 'https://kanjitisiki.com/search/search.php'
    data = {'kensaku':kanji_freq[i], 'how':'kanji'}
    resp = requests.post(url, data=data)
    if "該当する漢字・部首がありません" not in resp.text:
        soup = BeautifulSoup(resp.text, features="html.parser")
        url = soup.find('body').find('li', attrs={'class':'kensaku-kanjionly'}).find('a')['href']
        soup = BeautifulSoup(urlopen(url),features="html.parser")
        naritachi = soup.find("h2",string='成り立ち')
        if naritachi is not None:
            result[6] = naritachi.find_next_sibling('p').text
    kanji_note = genanki.Note(
        model=kanji_model,
        fields = result
    )
    kanji_deck.add_note(kanji_note)
    print(result)

genanki.Package(kanji_deck).write_to_file('output.apkg')