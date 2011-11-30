import sys;
import os;
d=os.path.dirname(__file__)
dirList=os.listdir(d + '/site-packages/')
for fname in dirList:
    sys.path.append(d + '/site-packages/' + fname)

