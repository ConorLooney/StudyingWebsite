"""Useful functions for validating data;
 functions return true if the data is valid, false otherwise"""

def presence_check(data):
    if data is None:
        return False
    if type(data) == str and len(data) == 0:
        return False
    return True

def lookup_check(data, data_set):
    if data not in data_set:
        return False
    return True

def range_check_exclusive(data, min, max):
    return data > min and data < max

def is_string_float(string):
    try:
        float(string)
    except ValueError:
        return False
    else:
        return True