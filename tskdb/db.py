#!/usr/bin/env python
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.schema

Base = sqlalchemy.ext.declarative.declarative_base()

def loaddbsqlite(path):
    return loaddb('sqlite:///%s'%path)

def loaddb(constr):
    def get_model(metadata, tablename, modelname=None):
        if modelname is None:
            modelname = str(tablename)
        cls = type(modelname, (Base,), dict(
            __table__=sqlalchemy.Table(tablename, metadata, autoload=True)
        ))
        return cls
    engine = sqlalchemy.create_engine(constr)
    meta = sqlalchemy.MetaData(bind=engine)
    session = sqlalchemy.orm.create_session(bind=engine)
    class Empty:
        pass
    meta.tbcls = Empty()
    meta.reflect(bind=engine)
    for tn in meta.tables.keys():
        cls = None
        t = meta.tables[tn]
        if not list(t.primary_key):
            t.append_constraint(sqlalchemy.schema.PrimaryKeyConstraint(*list(t.columns)))
        cls = get_model(meta, tn)
        setattr(meta.tbcls, tn, cls)
    return meta, session

