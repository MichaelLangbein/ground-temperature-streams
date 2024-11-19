
from dataclasses import dataclass
import datetime


@dataclass
class Bbox:
    lonMin: float
    lonMax: float
    latMin: float
    latMax: float
    
    def toList(self):
        return [self.lonMin, self.latMax, self.lonMax, self.latMax]
    
    def toString(self):
        return f"{self.toList()}"
    
    def intersects(self, other: "Bbox"):
        return not (self.lonMax < other.lonMin
                or self.lonMin > other.lonMax
                or self.latMax < other.latMin
                or self.latMin > other.latMax)
    
    
@dataclass
class TimeRange:
    minTime: datetime.datetime
    maxTime: datetime.datetime
    
    def contains(self, time: datetime.datetime):
        return time >= self.minTime and time <= self.maxTime