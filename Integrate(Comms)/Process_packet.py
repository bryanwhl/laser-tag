from math import floor
import crc8

ASCII = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-=,."
LIMIT = 67

def clean_data(info):
    return (info[2:-1])

def clear_padding(data):
    while True:
        if (data[0] == '#'):
            data = data[1:]
        else:
            return data

def unpack_data(data):
    try:
        data_converted = []
        sensor_values = []
        for i in range (len(data)):
            data_converted.append(ASCII.index(data[i]))
        signs   = data_converted[0]
        sensor_values.append((data_converted[1] + data_converted[2]  * LIMIT + data_converted[3] * LIMIT * LIMIT)/100)
        sensor_values.append((data_converted[4] + data_converted[5]  * LIMIT + data_converted[6] * LIMIT * LIMIT)/100)
        sensor_values.append((data_converted[7] + data_converted[8]  * LIMIT + data_converted[9] * LIMIT * LIMIT)/100)
        sensor_values.append(data_converted[10] + data_converted[11] * LIMIT)
        sensor_values.append(data_converted[12] + data_converted[13] * LIMIT)
        sensor_values.append(data_converted[14] + data_converted[15] * LIMIT)
        
        for i in range(6):
            if (signs % 2 != 0):
                sensor_values[5-i] = -sensor_values[5-i]
            signs = floor(signs/2)
        return sensor_values
    except ValueError:
        return 0, 0, 0

def crc_check(data_string):
    hash = crc8.crc8()
    crc = data_string[-2:]
    data_string = data_string[2:-2]
    hash.update(bytes(data_string, "utf-8"))
    if (hash.hexdigest() == crc):
        return True
    else:
        return False