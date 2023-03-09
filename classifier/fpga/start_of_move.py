THRESHOLD = 100

def detect_start_of_move(move_list): # 2D array of 20 * 6 dimensions
    sum_of_first_10_readings = [0, 0, 0, 0, 0, 0]
    sum_of_next_10_readings = [0, 0, 0, 0, 0, 0]
    for attribute_idx in range(6):
        for reading_no in range(10):
            sum_of_first_10_readings[attribute_idx] += move_list[reading_no][attribute_idx]
        for reading_no in range(10, 20):
            sum_of_next_10_readings[attribute_idx] += move_list[reading_no][attribute_idx]
    difference = sum(sum_of_next_10_readings) - sum(sum_of_first_10_readings)
    print(difference)
    return difference > THRESHOLD
