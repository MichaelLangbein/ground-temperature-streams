
from dataclasses import dataclass
import datetime
from pyproj.transformer import Transformer


@dataclass
class Point:
    lon: float
    lat: float
    crs: str = "epsg:4326"

    def toCrs(self, newCrs: str):
        coordTransformer = Transformer.from_crs(
            self.crs, newCrs, always_xy=True)
        transformed = coordTransformer.transform(self.lon, self.lat)
        return Point(
            lon=transformed[0],
            lat=transformed[1],
            crs=newCrs,
        )


@dataclass
class Bbox:
    lonMin: float
    lonMax: float
    latMin: float
    latMax: float
    crs: str = "epsg:4326"

    def fromString(stringRep: str):
        withoutBrackets = stringRep.strip()[1:-1]
        values = withoutBrackets.split(",")
        return Bbox(
            lonMin=float(values[0]),
            latMin=float(values[2]),
            lonMax=float(values[1]),
            latMax=float(values[3]),
        )

    def fromPoints(bottomLeft: Point, topRight: Point):
        if bottomLeft.crs != topRight.crs:
            raise ValueError("Points must be in the same crs")
        return Bbox(
            lonMin=bottomLeft.lon,
            latMin=bottomLeft.lat,
            lonMax=topRight.lon,
            latMax=topRight.lat,
            crs=bottomLeft.crs
        )

    def toList(self):
        return [self.lonMin, self.latMin, self.lonMax, self.latMax]

    def toString(self):
        return f"{self.toList()}"

    def intersects(self, other: "Bbox"):
        return not (self.lonMax < other.lonMin
                    or self.lonMin > other.lonMax
                    or self.latMax < other.latMin
                    or self.latMin > other.latMax)

    def getOverlap(self, other: "Bbox"):
        if self.crs != other.crs:
            raise ValueError("Bboxes must be in the same crs")
        if not self.intersects(other):
            return None
        return Bbox(
            lonMin=max(self.lonMin, other.lonMin),
            latMin=max(self.latMin, other.latMin),
            lonMax=min(self.lonMax, other.lonMax),
            latMax=min(self.latMax, other.latMax),
            crs=self.crs
        )

    def center(self):
        return Point(
            crs=self.crs,
            lon=(self.lonMin + self.lonMax) / 2,
            lat=(self.latMin + self.latMax) / 2
        )

    def BottomLeft(self):
        return Point(
            lon=self.lonMin,
            lat=self.latMin,
            crs=self.crs
        )

    def topRight(self):
        return Point(
            lon=self.lonMax,
            lat=self.latMax,
            crs=self.crs
        )

    def toCrs(self, newCrs: str):
        return Bbox.fromPoints(
            bottomLeft=self.BottomLeft().toCrs(newCrs),
            topRight=self.topRight().toCrs(newCrs),
        )


@dataclass
class TimeRange:
    minTime: datetime.datetime
    maxTime: datetime.datetime

    def fromStrings(minTime: str, maxTime: str):
        return TimeRange(
            minTime=datetime.datetime.strptime(minTime, "%Y-%m-%d"),
            maxTime=datetime.datetime.strptime(maxTime, "%Y-%m-%d")
        )

    def contains(self, time: datetime.datetime):
        return time >= self.minTime and time <= self.maxTime

    def overlaps(self, other: "TimeRange"):
        return not (self.minTime > other.maxTime or self.maxTime < other.minTime)
