"""Useful functions for validating data;
 functions return true if the data is valid, false otherwise"""

def presence_check(data):
    if data is None:
        return False
    return True