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

def _load_tsk_fs_info(session, meta):
    fs_info = {}
    for num,fs in enumerate(session.query(meta.tbcls.tsk_fs_info).all()):
        fs_info[fs.obj_id] = (u'part{0}'.format(num), fs)
    return fs_info

def _load_tsk_file_layout(session, meta):
    layout = {}
    for fl in session.query(meta.tbcls.tsk_file_layout).all():
        if not layout.has_key(fl.obj_id):
            layout[fl.obj_id] = []
        layout[fl.obj_id].append(fl)
    return layout

def _load_tsk_files(self, session, meta, fs_info, layout):
    for _file in session.query(meta.tbcls.tsk_files).all():
        if _file.parent_path:
            fullpath = os.path.join(_file.parent_path, _file.name)
        else:
            fullpath = os.path.join(_file.name)
        fsoffset = 0
        if _file.fs_obj_id:
            fsnum = fs_info[_file.fs_obj_id][0]
            fsoffset = fs_info[_file.fs_obj_id][1].img_offset
            fullpath = os.path.join(fsnum, fullpath.lstrip('/'))
        splitedpath = fullpath.rstrip('/').split('/')
        # get this file layout
        _file.layout = []
        if layout.has_key(_file.obj_id):
            seq = 0
            for fl in layout[_file.obj_id]:
                if seq == fl.sequence: # use first good layout only
                    _file.layout.append((fsoffset+fl.byte_start,fl.byte_len))
                seq += 1
        # some meta_flags sugar
        _file.flags = Empty()
        _file.flags.alloc   = 1  & _file.meta_flags
        _file.flags.unalloc = 2  & _file.meta_flags
        _file.flags.used    = 4  & _file.meta_flags
        _file.flags.unused  = 8  & _file.meta_flags
        _file.flags.comp    = 16 & _file.meta_flags
        _file.flags.orphan  = 32 & _file.meta_flags
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
        if _file.mode and _file.meta_type:
            _file.mode |= types[_file.meta_type]
        # choose metadata priority
        if _file.flags.alloc: # undeleted goes first
            self[splitedpath].metadata.insert(0,_file)
        else:
            self[splitedpath].metadata.append(_file)

class TskTree(Tree):
    def __init__(self, dbpath=None):
        super(TskTree,self).__init__()
        self.metadata = []
        self.currentmetadata = None
        #load db
        if dbpath != None:
            meta, session = loaddbsqlite(dbpath)
            print ' loading tsk_fs_info'
            fs_info = _load_tsk_fs_info(session, meta)
            print ' loading tsk_file_layout'
            layout = _load_tsk_file_layout(session, meta)
            print ' loading tsk_files'
            _load_tsk_files(self, session, meta, fs_info, layout)
            self.freeze()
            self.clearfilters()

    def clearfilters(self):
        self.visible = True
        if self.metadata and len(self.metadata)>0:
            self.currentmetadata = self.metadata[0]
        for k in self.keys():
            self[k].clearfilters()

    def setfilter(self, fn):
        self.visible = False
        for i, m in reversed(list(enumerate(self.metadata))):
            if fn(m, i):
                self.visible = True
                self.currentmetadata = m
        for k in self.keys():
            self.visible |= self[k].setfilter(fn)
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

    def getattr(self):
        if not self.visible:
            raise OSError(2)
        if len(self.metadata) == 0:
                # we dont have metadata for this node, fake one
            ret = _buildattr()
        else: # len(self.metadata) >= 1:
            ret = _buildattr(self.currentmetadata)
        mustbedir = (len(self.keys()) > 0)
        if mustbedir:
            ret['st_mode'] |= 040000 # IFDIR
        if (ret['st_mode'] & 0170000) == 0: # file type not set
            ret['st_mode'] |= 0100000 # IFREG
        ret['st_mode'] |= 0777 # RWX for all
        return ret
    
    def readdir(self):
        for k in self.keys():
            if self[k].visible:
                yield (k.encode('utf8'), None, 0)

    def read(self, length, offset):
        skip = 0
        layout = self.currentmetadata.layout
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
