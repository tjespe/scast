#!/usr/bin/env python
import os

def clear():
    os.system("clear")

chars = ["A", "B", "C", "D"]
s_chars = ["a", "b", "c", "d"]
def i_to_c(i):
    return chars[i]
def c_to_i(c):
    return (c in chars and chars.index(c)) or (c in s_chars and s_chars.index(c)) or 0
