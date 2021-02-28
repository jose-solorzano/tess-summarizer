#
# This script generates a cross-match between Gaia DR2 and TESS targets.
#

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

tess_targets = pd.read_csv('/opt/data/tess/all-targets.csv', usecols=['TICID', 'Tmag', 'RA', 'Dec'])
tess_targets.drop_duplicates(subset=['TICID'], inplace=True)
tess_targets.rename(columns={'RA': 'tess_ra', 'Dec': 'tess_dec'}, inplace=True)
print('Tess targets: %d' % len(tess_targets))
print(tess_targets.columns)
gaia_targets = pd.read_csv('/opt/data/tess/gaiadr2-tmass-baseline.csv', usecols=['source_id', 'ra', 'dec', 'pmra', 'pmdec', 'phot_g_mean_mag', 'parallax', 'parallax_error', 'l', 'b'])
gaia_targets.drop_duplicates(subset=['source_id'], inplace=True)
print('Gaia targets: %d' % len(gaia_targets))
print(gaia_targets.columns)

# Empirical best match for TESS coordinates: J2020.5
offset_years = 5.0

def get_results_frame():
    print('Creating BallTree...')
    MAX_DISTANCE_1 = 1 / 3600
    MIN_DISTANCE_2 = 3 / 3600
    ra = gaia_targets['ra'].values
    dec = gaia_targets['dec'].values
    pmra = gaia_targets['pmra'].values
    pmdec = gaia_targets['pmdec'].values
    ra_in_tess = ra + (pmra / 3600000) * offset_years
    dec_in_tess = dec + (pmdec / 3600000) * offset_years
    ballTree = BallTree(np.transpose([ra_in_tess, dec_in_tess]))
    print('Searching BallTree...')
    distance_matrix, index_matrix = ballTree.query(tess_targets[['tess_ra', 'tess_dec']], 2)
    results_matrix = []
    gaia_ids = gaia_targets['source_id'].values
    tess_ids = tess_targets['TICID'].values
    assert len(tess_ids) == len(distance_matrix)
    count = 0
    print('Processing...')
    sum_distances = 0
    for idx in range(len(distance_matrix)):
        distances = distance_matrix[idx]
        gaia_indexes = index_matrix[idx]
        assert len(distances) == 2 and len(gaia_indexes) == 2
        if distances[0] <= MAX_DISTANCE_1 and distances[1] >= MIN_DISTANCE_2:
            distance_arcsec = distances[0] * 3600
            sum_distances += distance_arcsec
            results_matrix.append([gaia_ids[gaia_indexes[0]], tess_ids[idx], distance_arcsec])
            count += 1
    print('Matched %d targets out of %d' % (count, len(distance_matrix)))
    print('Mean angular distance: %.3f' % (sum_distances / count))
    return pd.DataFrame(results_matrix, columns=['source_id', 'TICID', 'ang_distance'])


results_frame = get_results_frame()
print('Initial cross-matched data frame length: %d' % len(results_frame))
results_frame.drop_duplicates(subset=['source_id'], keep=False, inplace=True)
print('Length after removal of source_id duplicates: %d' % len(results_frame))
results_frame = pd.merge(results_frame, gaia_targets, on='source_id', how='inner')
results_frame = pd.merge(results_frame, tess_targets, on='TICID', how='inner')
print('Length after joins: %d' % len(results_frame))
mag_diffs = results_frame['phot_g_mean_mag'] - results_frame['Tmag']
mag_diffs_mean = np.mean(mag_diffs)
mag_diffs_sd = np.std(mag_diffs)
print('Mag diffs mean, sd: [%.3f, %.4f] ' % (mag_diffs_mean, mag_diffs_sd,))
max_diff = mag_diffs_mean + mag_diffs_sd * 4
min_diff = mag_diffs_mean - mag_diffs_sd * 4
results_frame = results_frame[(mag_diffs <= max_diff) & (mag_diffs >= min_diff)]
print('Length after mag diff outlier removal: %d' % len(results_frame))
results_frame.to_csv('/opt/data/tess/tess-gaiadr2-crossmatch.csv', index=False)
print('Wrote results!')

