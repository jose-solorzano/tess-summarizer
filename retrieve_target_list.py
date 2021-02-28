#
# This script retrieves a target list from the MIT TESS site
# and concatenates the files. Results contain duplicates.
#

import requests
import io
import pandas as pd
from bs4 import BeautifulSoup

PAGE_URL = 'https://tess.mit.edu/observations/target-lists/'
page = requests.get(PAGE_URL)
soup = BeautifulSoup(page.content, 'html.parser')
results = soup.find_all('a')
frames = []
for result in results:
    if result.text == 'csv':
        csv_url = result['href']
        print('Reading ' + csv_url)
        s = requests.get(csv_url).content
        c = pd.read_csv(io.StringIO(s.decode('utf-8')), skiprows=range(0, 5))
        frames.append(c)
combined = pd.concat(frames)
combined.to_csv('d:\\opt\\data\\tess\\all-targets.csv', index=False)
print('Wrote results!')

