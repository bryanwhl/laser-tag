# Import block
import os
import pandas as pd
import numpy as np
import time
from math import sqrt
import matplotlib.pyplot as plt
from sklearn import metrics
from sklearn.metrics import mean_squared_error, mean_absolute_error
from pandas.plotting import scatter_matrix
from importlib import reload
from sklearn.feature_selection import VarianceThreshold
from collections import Counter
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

class Parser:

    def obtain_data_for_start_of_move(motionQueue, window_size):
        if window_size > len(motionQueue):
            print("obtain_data_for_start_of_move function call: window size is less than 10")
            return []
        flat_list = sum(motionQueue[:window_size], [])
        return flat_list

    def obtain_data_for_1s_of_action(motionQueue, number_of_readings_per_sec, window_size, slide_size):
        # forty_consecutive_readings = motionQueue[:number_of_readings_per_sec]
        flat_list = sum(motionQueue, [])
        output_list = []
        for window_start_index in range(0, number_of_readings_per_sec + window_size, slide_size):
            output_list.append(flat_list[window_start_index : window_start_index + window_size])
        
        return output_list

    def flatten_list(ls):
        return sum(ls, [])

    def test_parser(motionQueue, window_size):
        print("Motion Queue data: ")
        print("Motion Queue length: ", len(motionQueue))
        print(motionQueue)
        output = Parser.obtain_data_for_start_of_move(motionQueue, window_size)
        print("start_of_move data length: ", len(output))
        if (len(output)) == window_size * 6:
            print("Test passed!")
        else:
            print("Test failed!")

