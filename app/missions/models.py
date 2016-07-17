from string import digits
import re

class Mission:
    def __init__(self, missionName, worldName):
       missionInfo = [x.strip() for x in missionName.split('_')]
       self.missionName = missionName
       self.missiontype = missionInfo[1].translate({ord(k): None for k in digits})
       self.playerCount = re.sub("[^0-9]", "", missionInfo[1])
       self.missionWorld = worldName


    def __eq__(self, other):
        return self.missionName == other.missionName
