import json, io, re, requests
from bs4 import BeautifulSoup


def get_datasets(url):
    r = requests.get(url.format(0))
    soup = BeautifulSoup(r.text)
    href = soup.select('#block-system-main a')[-1]['href']
    last_page = int(re.match(r'.*page=(.*)', href).group(1))

    for page in range(last_page + 1):
        r = requests.get(url.format(page))
        soup = BeautifulSoup(r.text)
        for link in soup.select('h2 a'):
            yield link['href']


def get_metadata(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    metadata = dict()
    metadata['_url'] = url.format(d)

    for elem in soup.select('.datasetview_container .datasetview_row'):
        for field in elem.select('.field'):
            label = field.select('.field-label')[0].text[:-2]
            item_list = list()
            item = field.select('.field-item')
            if len(item) == 0:
                items = elem.select('.tag_list a')
                for i in items:
                    item_list.append(i.text.strip())
                metadata[label] = item_list
            else:
                metadata[label] = item[0].text.strip()
    return metadata


if __name__ == '__main__':
    base_url = 'http://daten.berlin.de{}'
    datasets_url = 'http://daten.berlin.de/datensaetze?page={}'
    documents_url = 'http://daten.berlin.de/dokumente?page={}'

    all_metadata = list()
    for d in get_datasets(datasets_url):
        m = get_metadata(base_url.format(d))
        m['_type'] = 'dataset'
        all_metadata.append(m)

    for d in get_datasets(documents_url):
        m = get_metadata(base_url.format(d))
        m['_type'] = 'document'
        all_metadata.append(m)

    with io.open('daten-berlin_metadata.json', 'w', encoding='utf8') as json_file:
        json_file.write(unicode(json.dumps(all_metadata, indent=2, sort_keys=True, ensure_ascii=False)))

    print( json.dumps(all_metadata, indent=2, sort_keys=True) )