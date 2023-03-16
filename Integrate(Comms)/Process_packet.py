from math import floor
import crc8

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
        signs   = int(data[0])
        value_1 = int(data[1:6]) / 100
        value_2 = int(data[6:11]) / 100
        value_3 = int(data[11:16]) / 100
        if (signs % 2 != 0):
            value_3 = -value_3
        if ((signs/2) % 2 != 0):
            value_2 = -value_2
        if ((floor(signs/2)/2) % 2 != 0):
            value_1 = -value_1
        return value_1, value_2, value_3
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