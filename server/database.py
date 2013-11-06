import sqlalchemy
    
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

class Sender(Base):
    __tablename__ = 'senders'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    ip_address = Column(String)
    
    call_stacks = relationship("CallStack", cascade="all", backref='senders')
  
    def __init__(self, name, ip_address):
        self.name = name
        self.ip_address = ip_address
      
    def __repr__(self):
        return ""

class MethodCall(Base):
    __tablename__ = 'method_calls'
    id = Column(Integer, primary_key=True)
    function = Column(String)
    class_name = Column(String)
    module = Column(String)
    
    call_stacks = relationship("CallStack", cascade="all", backref='method_calls')
  
    def __init__(self, profile_stats):
        self.function = profile_stats['function']
        self.class_name = profile_stats['class']
        self.module = profile_stats['module']
      
    def __repr__(self):
        return ""

class CallStack(Base):
    __tablename__ = 'call_stacks'
    id = Column(Integer, primary_key=True)
    method_call_id = Column(None, ForeignKey('method_calls.id'))
    sender_id = Column(None, ForeignKey('senders.id'))
    datetime = Column(Float)
    
    call_stack_items = relationship("CallStackItem", cascade="all", backref='call_stacks')
  
    def __init__(self, method_call_id, sender_id, profile_stats):
        self.method_call_id = method_call_id
        self.sender_id = sender_id
        self.datetime = profile_stats['datetime']
      
    def __repr__(self):
        return ""

class CallStackItem(Base):
    __tablename__ = 'call_stack_items'
    id = Column(Integer, primary_key=True)
    call_stack_id = Column(None, ForeignKey('call_stacks.id'))
    function_name = Column(String)
    line_number = Column(Integer)
    module = Column(String)
    total_calls = Column(Integer)
    native_calls = Column(Integer)
    cumulative_time = Column(Float)
    total_time = Column(Float)
  
    def __init__(self, call_stack_id, stats):
        self.call_stack_id = call_stack_id
        self.function_name = stats['function']['name']
        self.line_number = stats['function']['line']
        self.module = stats['function']['module']
        self.total_calls = stats['total_calls']
        self.native_calls = stats['native_calls']
        self.cumulative_time = stats['cumulative']
        self.total_time = stats['time']
      
    def __repr__(self):
        return ""

def create_db_and_connect():
    database = sqlalchemy.create_engine('postgresql://postgres:my_password@localhost/profile_stats')
    database.connect()
    return database

session = None

def setup_profile_database():
    try:
        db = create_db_and_connect()
    except:
        postgres = sqlalchemy.create_engine("postgresql://postgres:my_password@localhost/postgres")
        conn = postgres.connect()
        conn.execute("commit")
        conn.execute("create database profile_stats")
        conn.close()
        db = create_db_and_connect()
        
    Base.metadata.create_all(db)
    Session = sessionmaker(bind=db)
    global session
    session = Session()
        
def get_sender_id(sender_name, ip_address):
    sender_query = session.query(Sender).filter_by(name=sender_name)
    sender = None
    if sender_query.count() == 0:
        # Add new sender if does not exist
        sender = Sender(sender_name, ip_address)
        session.add(sender)
        session.commit()
    else:
        sender = sender_query.first()
    return sender.id

def get_method_call_id(profile_stats):
    method_call_query = session.query(MethodCall).filter_by(function=profile_stats['function'], 
                                                            class_name=profile_stats['class'], 
                                                            module=profile_stats['module'])
    method_call = None
    if method_call_query.count() == 0:
        # Add new sender if does not exist
        method_call = MethodCall(profile_stats)
        session.add(method_call)
        session.commit()
    else:
        method_call = method_call_query.first()
    return method_call.id

def push_stats_buffer(stats_buffer, sender_name, ip_address):
    sender_id = get_sender_id(sender_name, ip_address)
    
    for profile_stats in stats_buffer:
        method_call_id = get_method_call_id(profile_stats)
        call_stack = CallStack(method_call_id, sender_id, profile_stats)
        session.add(call_stack)
        session.commit()
        pstats = profile_stats['pstats']
        for stats in pstats:
            session.add(CallStackItem(call_stack.id, stats))
    session.commit()