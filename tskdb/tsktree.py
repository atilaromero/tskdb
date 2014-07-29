#!/usr/bin/env python
import os
from db import loaddbsqlite
from tree import Tree

def _buildattr(metadata=None):
    if metadata:
        return {'st_atime':metadata.atime or 0,
                'st_ctime':metadata.ctime or 0,
                'st_gid':metadata.gid or 0,
                'st_mode':metadata.mode or 0,
                'st_mtime':metadata.mtime or 0,
                'st_nlink':1,
                'st_size':metadata.size or 0,
                'st_uid':metadata.uid or 0,
            }
    else:
        return {'st_atime':0,
                'st_ctime':0,
                'st_gid':0,
                'st_mode':0,
                'st_mtime':0,
                'st_nlink':1,
                'st_size':0,
                'st_uid':0,
            }
        
class Empty:
    pass

class TskTree(Tree):
    def __init__(self, dbpath=None):
        super(TskTree,self).__init__()
        self.metadata = []
        #load db
        if dbpath != None:
            meta, session = loaddbsqlite(dbpath)
            print ' loading tsk_fs_info'
            self.fs_info = {}
            for num,fs in enumerate(session.query(meta.tbcls.tsk_fs_info).all()):
                self.fs_info[fs.obj_id] = (u'part{0}'.format(num), fs)
            print ' loading tsk_file_layout'
            layout = {}
            for fl in session.query(meta.tbcls.tsk_file_layout).all():
                if not layout.has_key(fl.obj_id):
                    layout[fl.obj_id] = []
                layout[fl.obj_id].append(fl)
            print ' loading tsk_files'
            for rec in session.query(meta.tbcls.tsk_files).all():
                if rec.parent_path:
                    fullpath = os.path.join(rec.parent_path, rec.name)
                else:
                    fullpath = os.path.join(rec.name)
                fsoffset = 0
                if rec.fs_obj_id:
                    fsnum = self.fs_info[rec.fs_obj_id][0]
                    fsoffset = self.fs_info[rec.fs_obj_id][1].img_offset
                    fullpath = os.path.join(fsnum, fullpath.lstrip('/'))
                splitedpath = fullpath.rstrip('/').split('/')
                # get this file layout
                rec.layout = []
                if layout.has_key(rec.obj_id):
                    seq = 0
                    for fl in layout[rec.obj_id]:
                        if seq == fl.sequence: # use first good layout only
                            rec.layout.append((fsoffset+fl.byte_start,fl.byte_len))
                        seq += 1
                # some meta_flags sugar
                rec.flags = Empty()
                rec.flags.alloc   = 1  & rec.meta_flags
                rec.flags.unalloc = 2  & rec.meta_flags
                rec.flags.used    = 4  & rec.meta_flags
                rec.flags.unused  = 8  & rec.meta_flags
                rec.flags.comp    = 16 & rec.meta_flags
                rec.flags.orphan  = 32 & rec.meta_flags
                # put file type in st_mode
                types = [0000000, # undef
                         0100000, # reg
                         0040000, # dir
                         0010000, # fifo
                         0020000, # chr
                         0060000, # blk
                         0120000, # lnk
                         0000000, # shad
                         0140000, # sock
                         0000000, # wht
                         0000000, # virt
                ]
                if rec.mode and rec.meta_type:
                    rec.mode |= types[rec.meta_type]
                # choose metadata priority
                if rec.flags.alloc: # undeleted goes first
                    self[splitedpath].metadata.insert(0,rec)
                else:
                    self[splitedpath].metadata.append(rec)
            self.freeze()
            self.clearfilters()

    def clearfilters(self):
        self.visible = True
        for k in self.keys():
            self[k].clearfilters()

    def setfilter(self, fn):
        self.visible = fn(self)
        for k in self.keys():
            temp = self[k].setfilter(fn)
            print k, temp
            self.visible |= temp
        return self.visible

    def __getitem__(self, key):
        if (isinstance(key,str) or isinstance(key,unicode)) and key.count('/') > 0:
            if key == '/':
                return self
            else:
                if isinstance(key,str):
                    key = key.decode('utf8')
                parts = key.strip('/').split('/')
                return super(TskTree,self).__getitem__(parts)
        else:
            return super(TskTree,self).__getitem__(key)

    def pickmetadata(self):
        if len(self.metadata)>0:
            return self.metadata[0] # picking first metadata found !!!!
        else:
            return None

    def getattr(self):
        if len(self.metadata) == 0:
                # we dont have metadata for this node, fake one
            ret = _buildattr()
        else: # len(self.metadata) >= 1:
            ret = _buildattr(self.pickmetadata())
        mustbedir = (len(self.keys()) > 0)
        if mustbedir:
            ret['st_mode'] |= 040000 # IFDIR
        if (ret['st_mode'] & 0170000) == 0: # file type not set
            ret['st_mode'] |= 0100000 # IFREG
        ret['st_mode'] |= 0777 # RWX for all
        return ret
    
    def readdir(self):
        for k in self.keys():
            print k, self[k].visible
            if self[k].visible:
                yield (k.encode('utf8'), None, 0)

    def read(self, length, offset):
        skip = 0
        layout = self.pickmetadata().layout
        result = []
        for o,l in layout:
            if offset > l: # not there yet                            
                offset = offset - l
            else: # offset inside len                                 
                if offset + length > l: # more chunks to read
                    result.append([o+offset,l - offset])
                    length = length - (l - offset)
                    offset = 0
                else: # last chunk
                    result.append([o+offset, length])
                    return result
        return result
