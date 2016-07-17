from app import db
from sqlalchemy import Column, ForeignKey, Integer, String, REAL, DateTime, Boolean, func
from sqlalchemy.orm import relationship

import re
from string import digits

class CmpMission(db.Model):
    __tablename__ = 'CmpMission'
    __bind_key__ = 'missionary'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    raw_name = Column(String, nullable=False)
    player_count = Column(Integer, nullable=False)
    world = Column(String, nullable=False)
    author = Column(String, nullable=False)
    mission_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    host_notes = Column(String, nullable=False)
    min_play = Column(Integer)
    created = Column(DateTime, nullable=False)
    update = Column(DateTime, nullable=True)
    folder = Column(String, nullable=False)

    def __init__(self, mission_name, mission_world, mission_author, raw_name, status, host_notes, min_play, created, folder):
        missionInfo = [x.strip() for x in mission_name.split('_')]
        self.name = mission_name
        self.player_count = re.sub("[^0-9]", "", missionInfo[1])
        self.world = mission_world
        self.author = mission_author
        self.mission_type = missionInfo[1].translate({ord(k): None for k in digits})
        self.status = status
        self.raw_name = raw_name
        self.host_notes = host_notes
        self.min_play = min_play
        self.created = created
        self.update = None
        self.folder = folder

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return self.name
