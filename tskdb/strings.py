#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import pdb
import datetime
import collections
import plac
import tsktree
import db

grps=[u'abcdefghijklmnopqrstuvwxyz',
      u'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
      u'0123456789',
      u'ç',u'Ç',
      u'áéíóú',u'ÁÉÍÓÚ',
      u'àèìòù',u'ÀÈÌÒÙ',
      u'âêîôû',u'ÂÊÎÔÛ',
      u'ãõ',#ẽĩũ',
      u'ÃÕ',#ẼĨŨ',
      u'äëïöü',u'ÄËÏÖÜ',
      #u' -.,/:"'+u"'",
      ]
chars=u''.join(grps)
encodings=['latin1',
           'utf8',
           'utf_16_le','utf_16_be',
           'utf_32_le','utf_32_be',]
for c in chars:
    assert len(c.encode('utf8'))==1 or c.encode('utf8')[0]=='\xc3'
    assert '\x00'+c.encode('latin1')==c.encode('utf_16_be')
    assert '\x00\x00\x00'+c.encode('latin1')==c.encode('utf_32_be')
    assert c.encode('latin1')+'\x00'==c.encode('utf_16_le')
    assert c.encode('latin1')+'\x00\x00\x00'==c.encode('utf_32_le')
regsexpr={}
regsexpr['utf8']='[a-zA-Z0-9]|\xc3[%s]'%(''.join([d[1] for d in [c.encode('utf8') for c in chars] if len(d)>1]))
regsexpr['latin1']='[%s]'%(''.join([c.encode('latin1') for c in chars]))
regsexpr['utf_16_be']='\x00[%s]'%(''.join([c.encode('latin1') for c in chars]))
regsexpr['utf_32_be']='\x00\x00\x00[%s]'%(''.join([c.encode('latin1') for c in chars]))
regsexpr['utf_16_le']='[%s]\x00'%(''.join([c.encode('latin1') for c in chars]))
regsexpr['utf_32_le']='[%s]\x00\x00\x00'%(''.join([c.encode('latin1') for c in chars]))
    
import multiprocessing
import multiprocessing.dummy

def _strings_producer(srcpath, queue, blksize):
    with open(srcpath) as f:
        while True:
            chunk = f.read(blksize)
            queue.put(chunk, True)
            if len(chunk) == 0:
                break

def strings(encoding,srcpath,minimum=5,maximum=20):
    blksize = 1024**2 #1MB
    queue = multiprocessing.Queue(40) #40MB
    recall=21*5
    regs={}
    for x in encodings:
        regs[x]=re.compile('(?:%s){%s,%s}'%(regsexpr[x],minimum,maximum+1))
    producer = multiprocessing.dummy.Process(target=_strings_producer, args=(srcpath, queue, blksize))
    producer.daemon = True
    producer.start()
    bl1=bl2=''
    t1=t2=datetime.datetime.now()
    pos={}
    offset=0
    while True:
        if len(bl1)>recall:
            skip=len(bl1)-recall
        else:
            skip=len(bl1)
        t2=datetime.datetime.now()
        deltat=t2-t1
        speed=(skip/1024**2)/deltat.total_seconds()
        sys.stderr.write('    %4.2fMB\t%1.2fMB/s\r'%(offset/1024.0**2,speed))
        t1=t2
        offset+=skip
        bl1=bl1[skip:]+bl2
        bl2=queue.get(True)
        if len(bl2)==0: # EOF
            for k in sorted(pos.keys()):
                yield k,pos.pop(k)
            break
        blt=bl1+bl2
        for x in [encoding,]:
            for found in regs[x].finditer(blt):
                position=found.start()+offset
                try:
                    pass
                    text=found.group().decode(x)
                    if len(text)>maximum:
                        continue
                except:
                    print 'blt',[blt,]
                    print [found.string,]
                    pdb.set_trace()
                if pos.has_key(position):
                    if len(text)>len(pos[position]):
                        pos[position]=text
                else:
                    pos[position]=text
        for k in sorted(pos.keys()):
            if k<offset:
                yield k,pos.pop(k)

def printfound(position,text,files):
    line = u'\t'.join([unicode(position),unicode(text)]+files)
    line += u'\n'
    sys.stdout.write(line.encode('utf8'))

def getlayout(metadata, idx):
    return metadata.layout

DMap = collections.namedtuple('DMap',['offset', 'length', 'path'])

import bisect

def main(encoding, ddpath, dbpath):
    """
    Usage:
        python strings.py (utf8|utf_16_le) FILE [FILE [FILE [...]]]

    Like linux 'strings', but understands some diacritics and uses tskdb to find filenames.
    """
    t = tsktree.TskTree(dbpath)
    diskmap = {}
    for path, layouts in t.runonchildren(getlayout):
        for offset, length in layouts:
            if not diskmap.has_key(offset):
                diskmap[offset] = []
            diskmap[offset].append(DMap(offset, length, path))
    diskmapidx = sorted(diskmap.keys())
    for k,text in strings(encoding,ddpath):
        off = diskmapidx[bisect.bisect_right(diskmapidx,k) - 1]
        files = []
        for dmap in diskmap[off]:
            if off + dmap.length >= k:
                files.append(dmap.path)
        printfound(k,text,files)

if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
