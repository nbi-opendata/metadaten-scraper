import json, io, re, requests
from bs4 import BeautifulSoup
from datetime import datetime


def get_datasets(url):
    r = requests.get(url.format(0))
    soup = BeautifulSoup(r.text)
    href = soup.select('#block-system-main a')[-1]['href']
    last_page = int(re.match(r'.*page=(.*)', href).group(1))

    for page in range(last_page + 1):
        print( '[DEBUG] page:', page )
        r = requests.get(url.format(page))
        soup = BeautifulSoup(r.text)
        for link in soup.select('h2 a'):
            yield (link['href'], link.text)


def get_metadata(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    metadata = dict()
    metadata['_url'] = url.format(d)
    metadata['_collection_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for elem in soup.select('.datasetview_container .datasetview_row'):
        for field in elem.select('.field'):
            label = field.select('.field-label')[0].text[:-2]
            item_list = list()
            item = field.select('.field-item')
            if label == 'Website':
                metadata[label] = item[0].select('a')[0]['href']
            elif len(item) == 0:
                items = elem.select('.tag_list a')
                for i in items:
                    item_list.append(i.text.strip())
                metadata[label] = item_list
            else:
                metadata[label] = item[0].text.strip()

    tags = set()
    for elem in soup.select('.post_tags.tag_list a'):
        tags.add(elem.text.strip())
    metadata['tags'] = list(tags)

    return metadata


if __name__ == '__main__':
    base_url = 'http://daten.berlin.de{}'
    datasets_url = 'http://daten.berlin.de/datensaetze?page={}'
    documents_url = 'http://daten.berlin.de/dokumente?page={}'

    all_labels = set()
    all_metadata = list()
    done_datasets = set()

    # iterate over all dataset urls
    for d, t in get_datasets(datasets_url):
        if d in done_datasets:
            print('skip', d)
            continue  # skip datasets
        m = get_metadata(base_url.format(d))
        m['_type'] = 'dataset'
        m['_title'] = t
        all_metadata.append(m)
        for k in m.keys(): all_labels.add(k)
        print(json.dumps(m, sort_keys=1, ensure_ascii=False))
        done_datasets.add(d)

    # iterate over all document urls
    for d, t in get_datasets(documents_url):
        if d in done_datasets:
            print('skip', d)
            continue  # skip datasets
        m = get_metadata(base_url.format(d))
        m['_type'] = 'document'
        m['_title'] = t
        all_metadata.append(m)
        for k in m.keys(): all_labels.add(k)
        print(json.dumps(m, sort_keys=1, ensure_ascii=False))
        done_datasets.add(d)


    # write json file
    with io.open('daten-berlin_metadata.json', 'w', encoding='utf8') as json_file:
        json_file.write((json.dumps(all_metadata, indent=2, sort_keys=True, ensure_ascii=False)))

    # write csv
    with open('daten-berlin_metadata.csv', 'wb') as csv_file:
        for l in sorted(all_labels):
            csv_file.write((l + ';').encode('utf8'))
        csv_file.write('\n'.encode('utf8'))
        for m in all_metadata:
            for l in sorted(all_labels):
                if l in m:
                    csv_file.write(str(m[l]).encode('utf8'))
                csv_file.write(';'.encode('utf8'))
            csv_file.write('\n'.encode('utf8'))