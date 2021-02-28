#
# This script downloads the latest MAST TOI catalog and TCE data.
# The data is summarized, such that we're only left with TCE counts per target,
# and various 1/0 flags derived by matching common patterns in the
# Public Comments field of the TOI.
#

import requests
import io
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from comment_matching import *

# Download TOI catalog

tois_content = requests.get('https://archive.stsci.edu/missions/tess/catalogs/toi/tois.csv').content
tois_table = pd.read_csv(io.StringIO(tois_content.decode('utf-8')), skiprows=range(0, 4), usecols=['TIC', 'Public Comment'])
tois_summary_map = dict()
for index, row in tois_table.iterrows():
    tic = row['TIC']
    comment = row['Public Comment']
    if comment != comment:
        # Is NA/NaN
        comment = ''

    blank = comment is None or comment == ''
    eb = is_eb(comment)
    variable = is_variable(comment)
    oddeven = is_oddeven(comment)
    vshaped = is_vshaped(comment)
    shoulders = is_shoulders(comment)

    summary_row = tois_summary_map.get(tic)
    if summary_row is None:
        summary_row = [tic, 1, 0, 0, 0, 0, 0, 0]
        tois_summary_map[tic] = summary_row
    if eb:
        summary_row[2] = 1
    if variable:
        summary_row[3] = 1
    if oddeven:
        summary_row[4] = 1
    if vshaped:
        summary_row[5] = 1
    if shoulders:
        summary_row[6] = 1
    if blank:
        summary_row[7] = 1
summary_tois = pd.DataFrame(tois_summary_map.values(), columns=['TICID', 'is_toi', 'eb', 'variable', 'odd_even', 'v_shaped', 'shoulders', 'blank'])
print('Length of TOI summary frame: %d' % len(summary_tois))

# Download TCE data

PAGE_URL = 'https://archive.stsci.edu/tess/bulk_downloads/bulk_downloads_tce.html'
page = requests.get(PAGE_URL)
soup = BeautifulSoup(page.content, 'html.parser')
results = soup.find_all('a')
id_counts = dict()
visited_tce_ids = set()
duplicate_count = 0
for result in results:
    if result.text.endswith('tcestats.csv'):
        csv_uri = result['href']
        csv_url = urljoin(PAGE_URL, csv_uri)
        print('Reading ' + csv_url)
        s = requests.get(csv_url).content
        c = pd.read_csv(io.StringIO(s.decode('utf-8')), skiprows=range(0, 6), usecols=['ticid', 'tceid'])
        tids = c['ticid'].values
        tceids = c['tceid'].values
        for i in range(len(tids)):
            tid = tids[i]
            tceid = tceids[i]
            if tceid in visited_tce_ids:
                duplicate_count += 1
            else:
                visited_tce_ids.add(tceid)
                id_count = id_counts.get(tid)
                if id_count is None:
                    id_counts[tid] = 1
                else:
                    id_counts[tid] = id_count + 1


print('Duplicate TCEs: %d' % duplicate_count)
results_frame = pd.DataFrame.from_dict(id_counts, orient='index', columns=['TCE_Count'])
results_frame['TICID'] = results_frame.index
print('Length of TCE summary frame: %d' % len(results_frame))

# Join the two frames

joined_data = pd.merge(results_frame, summary_tois, how='outer', on='TICID').fillna(0)
print('Length of joined summary frame: %d' % len(joined_data))
joined_data.drop_duplicates(subset=['TICID'], inplace=True)
print('Length after dropping duplicates: %d' % len(joined_data))

# Write results

joined_data.to_csv('d:\\opt\\data\\tess\\summarized-tess-tce-toi.csv', index=False)
print('Wrote results!')
