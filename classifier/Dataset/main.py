from pynq import Overlay

import pynq.lib.dma
from pynq import DefaultIP
from pynq import allocate
import numpy as np
from struct import unpack, pack
import time

cols_to_keep = [
    'tBodyAcc-mean()-X',
    'tBodyAcc-mean()-Y',
    'tBodyAcc-mean()-Z',
    'tBodyGyro-mean()-X',
    'tBodyGyro-mean()-Y',
    'tBodyGyro-mean()-Z',
    'Activity',
]

overlay = Overlay('./final_2.bit')
in_buffer = allocate(shape=(120,), dtype=np.int32)
test_df_raw = pd.read_csv('./test.csv', index_col=False)

test_df_raw = test_df_raw[test_df_raw.Activity != 'SITTING']
test_df_raw = test_df_raw[test_df_raw.Activity != 'LAYING']

test_df_raw.reset_index(inplace=True)

test_df = test_df_raw[cols_to_keep]

def split_df(df):
    features = df.drop('Activity', axis=1)
    labels = df['Activity']
    return features, labels

test_features_df, test_labels_df = split_df(train_df)

WINDOW_SIZE = 20
SLIDE_SIZE = 1

def process_df_with_sliding_window(df, window_size, slide_size):
    attributes = ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]
    columns_list = []
    # Build column list
    for idx in range(1, 1 + window_size):
        for attribute in attributes:
            columns_list.append(attribute + '_' + str(idx))
            
    df_out = pd.DataFrame(columns=columns_list)

    for row_idx in range(0, len(df) - window_size, slide_size):
        curr_window_data = []
        for row_iter_idx in range(window_size):
            curr_row_idx = row_idx + row_iter_idx
            curr_row_list = df.loc[curr_row_idx, :].values.flatten().tolist()
            curr_window_data += curr_row_list

        df_out.loc[len(df_out)] = curr_window_data

    return df_out