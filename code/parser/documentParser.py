import re
from string import punctuation
from unicodedata import normalize

import pandas as pd
from ioc_finder import find_iocs
from tika import parser

from utilities import iocextract


def parse_document(document_path, keywords=[], report_title=None):
    parsedDocument = parser.from_file(document_path)
    keywords_argument = []
    title = []
    for elem in parsedDocument.keys():
        if isinstance(parsedDocument[elem], dict):
            for key in parsedDocument[elem]:
                if ("key" in key.lower()):
                    keywords_argument = parsedDocument[elem][key]
                if ("title" in key.lower()):
                    title = parsedDocument[elem][key]
                if isinstance(parsedDocument[elem][key], dict):
                    for key2 in parsedDocument[elem][key]:
                        if ("key" in key2.lower()):
                            keywords_argument = parsedDocument[elem][key][key2]
                        if ("title" in key.lower()):
                            title = parsedDocument[elem][key][key2]

    if ('content' not in parsedDocument):
        return None
    if (parsedDocument['content'] is None):
        return None
    raw_text = parsedDocument['content'].lower()
    remove_punct_map = dict.fromkeys(map(ord, punctuation))
    text = raw_text.translate(remove_punct_map)
    text = text.replace("\n\n", " ").replace("\n", "").replace("•", "")
    result = pd.DataFrame(columns={"md5", "sha1", "sha256", "sha512"})
    keywords_list = []
    keywords_title = []
    for elem in title:
        if (elem in keywords):
            keywords_title.append(elem)
    if report_title is not None:
        for elem in report_title:
            if (elem in keywords):
                keywords_title.append(elem)
    for elem in keywords_argument:
        if (elem in keywords):
            keywords_title.append(elem)

    iocextract_result = iocextract.extract_iocs_dict(raw_text, refang=True, strip=True)
    url_list = set(
        [normalize('NFKD', x).encode('ASCII', 'ignore').decode('ASCII', 'ignore') for x in iocextract_result["url"] if
         not normalize('NFKD', x).encode('ASCII', 'ignore').endswith(b"-")])
    ip_list = set([x for x in iocextract_result["ip"] if not x.startswith(('192.168.', '10.', '172.16.', '172.31.'))])
    email = set(iocextract_result["email"])
    for elem in ([{"md5": hash, "sha1": None, "sha256": None, "sha512": None} for hash in iocextract_result["md5"]]):
        result = result.append(elem, ignore_index=True)

    for elem in ([{"md5": None, "sha1": hash, "sha256": None, "sha512": None} for hash in iocextract_result["sha1"]]):
        result = result.append(elem, ignore_index=True)

    for elem in ([{"md5": None, "sha1": None, "sha256": hash, "sha512": None} for hash in iocextract_result["sha256"]]):
        result = result.append(elem, ignore_index=True)

    for elem in ([{"md5": None, "sha1": None, "sha256": None, "sha512": hash} for hash in iocextract_result["sha512"]]):
        result = result.append(elem, ignore_index=True)

    cve_list = find_iocs(raw_text).get("cves")

    if len(keywords_title) == 0:
        for elem in keywords:
            if re.search(r'\b({})\b'.format(elem), text):
                keywords_list.append(elem)
    return {"keyword": keywords_list, "hash": result, "email": email, "ip": ip_list, "url": url_list, "cve": cve_list}
