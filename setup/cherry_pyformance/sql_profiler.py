import time
import inspect
from cherry_pyformance import cfg, stat_logger


sql_stats_buffer = {}


###============================================================###

class CursorWrapper(object):

    def __setattr__(self, name, value):
        setattr(self._cursor, name, value)

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __iter__(self):
        return iter(self._cursor)

    def execute(self, sql, *args, **kwargs):
        if not sql.startswith('PRAGMA'):
            return profile_sql(self._cursor.execute, sql, *args, **kwargs)
        else:
            return self._cursor.execute(sql, *args, **kwargs)

    def executemany(self, sql, *args, **kwargs):
        if not sql.startswith('PRAGMA'):
            return profile_sql(self._cursor.executemany, sql, *args, **kwargs)
        else:
            return self._cursor.executemany(sql, *args, **kwargs)

class ConnectionWrapper(object):

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        return self._connection.__exit__(*args, **kwargs)

    def cursor(self, *args, **kwargs):
        return Psycopg2CursorWrapper(self._connection.cursor(*args, **kwargs), self._connect_params, (args, kwargs))

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

###============================================================###

class Psycopg2CursorWrapper(CursorWrapper):

    def __init__(self, cursor, connect_params=None, cursor_params=None):
        object.__setattr__(self, '_cursor', cursor)
        object.__setattr__(self, '_connect_params', connect_params)
        object.__setattr__(self, '_cursor_params', cursor_params)
        object.__setattr__(self, 'fetchone', cursor.fetchone)
        object.__setattr__(self, 'fetchmany', cursor.fetchmany)
        object.__setattr__(self, 'fetchall', cursor.fetchall)

    def callproc(self, procname, *args, **kwargs):
        if not script.startswith('PRAGMA'):
            return profile_sql(self._cursor.executescript, script, *args, **kwargs)
        else:
            return self._cursor.executescript(script, *args, **kwargs)

class Psycopg2ConnectionWrapper(ConnectionWrapper):

    def __init__(self, connection, connect_params=None):
        self._connection = connection
        self._connect_params = connect_params

    def cursor(self, *args, **kwargs):
        return Psycopg2CursorWrapper(self._connection.cursor(*args, **kwargs), self._connect_params, (args, kwargs))

class Psycopg2ConnectionFactory(object):

    def __init__(self, connect):
        self.__connect = connect

    def __call__(self, *args, **kwargs):
        return Psycopg2ConnectionWrapper(self.__connect(*args, **kwargs), (args, kwargs))

###============================================================###

class SqliteCursorWrapper(CursorWrapper):

    def __init__(self, cursor):
        object.__setattr__(self, '_cursor', cursor)
        object.__setattr__(self, 'fetchone', cursor.fetchone)
        object.__setattr__(self, 'fetchmany', cursor.fetchmany)
        object.__setattr__(self, 'fetchall', cursor.fetchall)

    def executescript(self, script, *args, **kwargs):
        if not script.startswith('PRAGMA'):
            return profile_sql(self._cursor.executescript, script, *args, **kwargs)
        else:
            return self._cursor.executescript(script, *args, **kwargs)

class SqliteConnectionWrapper(ConnectionWrapper):

    def __init__(self, connection):
        self._connection = connection

    def cursor(self, *args, **kwargs):
        return SqliteCursorWrapper(self._connection.cursor(*args, **kwargs))

    def execute(self, sql, *args, **kwargs):
        if not sql.startswith('PRAGMA'):
            return profile_sql(self._connection.execute, sql, *args, **kwargs)
        else:
            return self._connection.execute(sql, *args, **kwargs)

    def executemany(self, sql, *args, **kwargs):
        if not sql.startswith('PRAGMA'):
            return profile_sql(self._connection.executemany, sql, *args, **kwargs)
        else:
            return self._connection.executemany(sql, *args, **kwargs)

    def executescript(self, script, *args, **kwargs):
        if not script.startswith('PRAGMA'):
            return profile_sql(self._connection.executescript, script, *args, **kwargs)
        else:
            return self._connection.executescript(script, *args, **kwargs)

class SqliteConnectionFactory(object):

    def __init__(self, connect):
        self.__connect = connect

    def __call__(self, *args, **kwargs):
        return SqliteConnectionWrapper(self.__connect(*args, **kwargs))

###============================================================###

def profile_sql(action, sql, *args, **kwargs):
    start_time = time.time()
    start_clock = time.clock()
    output = action(sql, *args, **kwargs)
    end_clock = time.clock()
    time_diff = end_clock-start_clock
    if time_diff > 0:
        stack = inspect.stack()
        for i in range(len(stack)):
            stack[i] = {'module': stack[i][1], 'function': stack[i][3]}
        _id = id(start_time)
        sql_stats_buffer[_id] = {'datetime':start_time,
                                 'duration':time_diff,
                                 'stack':stack,
                                 'sql_string':sql,
                                 'args':args[0] if len(args)>0 else []
                                }
        del stack
    return output

def decorate_connections():
    if cfg['sql']['database'] == 'sqlite':
        import sqlite3
        setattr(sqlite3,'connect', SqliteConnectionFactory(sqlite3.connect))
        setattr(sqlite3.dbapi2,'connect', SqliteConnectionFactory(sqlite3.dbapi2.connect))
    elif cfg['sql']['database'] == 'postgres':
        import psycopg2
        setattr(psycopg2,'connect', Psycopg2ConnectionFactory(psycopg2.connect))
    else:
        raise Exception('Unknown/Unsupported database profile type.')

