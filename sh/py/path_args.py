"""
Input: argv
Output: stdout, all elements of argv following ` -- `, one per line.
"""


import sys
import itertools

args = list(itertools.dropwhile(lambda arg: arg != '--', sys.argv))[1:]

print(*args, sep='\n')
