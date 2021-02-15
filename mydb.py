#!/usr/bin/env python

import MySQLdb

class DisconnectSafeCursor(object):
    db = None
    cursor = None

    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def close(self):
        self.cursor.close()

    def execute(self, *args, **kwargs):
        try:
            return self.cursor.execute(*args, **kwargs)
        except MySQLdb.OperationalError:
            self.db.reconnect()
            self.cursor = self.db.cursor()
            return self.cursor.execute(*args, **kwargs)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchmany(self, size):
        return self.cursor.fetchmany(size)

    def fetchall(self):
        return self.cursor.fetchall()

class DisconnectSafeConnection(object):
    connect_args = None
    connect_kwargs = None
    conn = None

    def __init__(self, *args, **kwargs):
        self.connect_args = args
        self.connect_kwargs = kwargs
        self.reconnect()

    def reconnect(self):
        self.conn = MySQLdb.connect(*self.connect_args, **self.connect_kwargs)

    def cursor(self, *args, **kwargs):
        cur = self.conn.cursor(*args, **kwargs)
        return DisconnectSafeCursor(self, cur)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

disconnectSafeConnect = DisconnectSafeConnection