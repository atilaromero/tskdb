#!/usr/bin/env python
import os
import datetime
import collections
from db import loaddbsqlite
from tree import Tree, Compare

def findfiles(meta,session,path):
    tsk_files=meta.tbcls.tsk_files
    for f in session.query(tsk_files)\
                    .filter(tsk_files.parent_path.startswith(path))\
                    .filter(tsk_files.meta_type==1)\
                    .filter(tsk_files.size>0)\
                    .all():
        yield f.mtime,os.path.join(f.parent_path.split(path,1)[1],f.name)

def main():
    meta,session=loaddbsqlite('M132377.db')
    path='/$RECYCLE.BIN/S-1-5-21-1926605686-1883886638-4266838064-1001/$RCFBY9L/'
    A=findfiles(meta,session,path)
    meta,session=loaddbsqlite('M132379.db')
    path='/Arquivos/Leo/files/'
    B=findfiles(meta,session,path)
    C=loadtimes('M132383-pasta.times')
    A5=loadmd5('77.md5')
    B5=loadmd5('M132379.md5')
    C5=loadmd5('M132383-pasta.md5')
    data=collections.defaultdict(lambda:(['','',''],['','','']))
    for i,x in enumerate([A,B,C]):
        for mtime,path in x:
            data[path][0][i]=datetime.date.fromtimestamp(mtime)
    for i,x in enumerate([A5,B5,C5]):
        for md5,path in x:
            data[path][1][i]=md5
    result=Compare()
    for k in sorted(data.keys()):
        pos=k.split('/')
        result.position(pos).dates=data[k][0]
        result.position(pos).md5s=data[k][1]
    #for k in sorted(data.keys()):
    #    print compare(data[k][0])\
    #        ,compare(data[k][1])\
    #        ,k
    return result

def t1(result,x,y):
    for k in sorted(result.keys()):
        print result[k].getdateequal(x,y)\
            ,result[k].getmd5equal(x,y)\
            ,result[k].getainb(x,y)\
            ,result[k].strdates(x,y)\
            ,result[k].strmd5s(x,y)\
            ,k

def filelist2tree(filelist):
    result=Tree()
    for f in filelist:
        if f:
            parts=f.split('/')
            result.pos(parts)
    return result


def loadmd5(filepath):
    with open(filepath) as f:
        for line in f:
            if line:
                md5=line[:32]
                path=line[34:].rstrip().decode('utf8')
                yield md5,path

def compare(arr):
    result=''
    for i,x in enumerate(arr):
        res=' '
        if x:
            for j,y in enumerate(arr):
                if not i==j:
                   if x==y or res=='=':
                       res='='
                   else:
                       res='!'
        result+=res
    return result

def listtimes(pathdir):
    for r,ds,fs in os.walk(pathdir):
        for f in fs:
             rf=os.path.join(r,f)
             rfstat=os.stat(rf)
             yield rfstat.st_atime,rfstat.st_mtime,rfstat.st_ctime,rf.split('%s/'%pathdir,1)[1]

def savetimes(pathdir,outfile):
    with open(outfile,'w') as fil:
        for x in listtimes(pathdir):
            fil.write('\t'.join(map(str,x)))
            fil.write('\n')

def loadtimes(filepath):
    with open(filepath) as f:
        for line in f:
            if line:
                x=line.decode('utf8').rstrip().split('\t',3)
                yield int(float(x[1])),x[3]
