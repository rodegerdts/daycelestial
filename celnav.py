# -*- coding: cp1252 -*-

''' Celestial Navigation.

The celnav module provides classes and functions usefull for celestial navigation.
Needs PyEphem'''

import ephem
import math


class Sight:
    '''The sight class takes values of a singel sextant sight and executes calculations.

    Input parameters:
        longitude of AP
        latitude of AP
        what kind of object
        the sextant altitude Hs without index error
        date and time of sight
        elevation above sea level'''
    
    def __init__(self, aplon, aplat, target="sunll", Hs=0, time="2012", elev=0, temp=20, press=1013):
        self.aplon=(aplon)
        self.aplat=(aplat)
        self.target=target
        self.Hs=Hs
        self.time=ephem.date(time)
        self.elev = elev
        self.temperature = temp
        self.pressure = press


        
        self.ap = ephem.Observer()
        self.ap.lon = self.aplon
        self.ap.lat = self.aplat
        self.ap.elevation = self.elev
        self.ap.date = self.time
        self.ap.temp = self.temperature
        self.ap.pressure = self.pressure
        
        if self.target == ("sunll"):
            self.o = ephem.Sun()
            self.cordir = -1
        elif self.target == ("sunul"):
            self.o = ephem.Sun()
            self.cordir = 1
        elif self.target ==("moonll"):
            self.o = ephem.Moon()
            self.cordir = -1
        elif self.target ==("moonul"):
            self.o = ephem.Moon()
            self.cordir = 1
        elif self.target == "venus":
            self.o = ephem.Venus()
            self.cordir = 0
        else:
            print "target error %s" %(target)
            

        self.o.compute(self.ap)
        self.Dip = 1.76*math.pi/10800*math.sqrt(self.elev)
        self.Ho = self.Hs - self.Dip
##        print "Dip: %f" %self.Dip
##        print "altitude: %s" %self.o.alt
##        print "azimut: %s" %self.o.az
##        print "time %s" %self.ap.date
##        print "aplon: %s" %self.ap.lon
        
        
    def getalt(self):       
        '''Returns Hc.'''
        return ephem.degrees(self.o.alt + (self.o.radius * self.cordir))

    def getaz(self):        
        '''Returns azimu til Hc.'''
        return self.o.az

    def gettime(self):      
        '''Retrns the time of sight as an ephem.date.'''
        return self.time

    def getintercept(self): 
        '''Returns the intercept.'''
        return self.Ho-(self.o.alt + (self.o.radius * self.cordir))

    def getlon(self):       
        '''Returns the AP longitude'''
        return self.aplon

    def getlat(self):       
        '''Retrns the AP latitude'''
        return self.aplat

    def setlon(self, lon):
        '''Set the longgitude of the AP'''
        self.aplon= lon
        self.ap.lon = lon
        self.o.compute(self.ap)

    def setlat(self, lat):
        '''Set the latitude of the AP'''
        self.aplat= lat
        self.ap.lat= lat
        self.o.compute(self.ap)
        





        
def deadRec(lon, lat, dist, heading):
    '''Dead reconing using planar geometry.

    must not be used for longer distances!
    Input last known position distance in NM, and true heading over ground in radiands or an ephem.angel.'''
    
    drlon=ephem.degrees(lon+(float(dist)/60/180*math.pi)*math.sin(heading)/math.cos(lat))
    drlat=ephem.degrees(lat+(float(dist)/60/180*math.pi)*math.cos(heading))
    return [drlon, drlat]




def compfix (s1, s2, speed=0, hdg=0):
    '''Compute a running fix from to sights.

    Uses planar geometry but compensates with iteration over intercepts.'''
    timediff = (s2.gettime() - s1.gettime())*24
    print "timediff:%f " %timediff
    distance = timediff*speed
    print "distance: %f" %distance
    drpos = deadRec(s1.getlon(), s1.getlat(), distance, hdg)
    print "drpos: %s   %s" %(drpos[0], drpos[1])
    s2.setlon(drpos[0])
    s2.setlat(drpos[1])
    i2 = s1.getintercept()
    i1 = s2.getintercept()
    while i1 > math.fabs(ephem.degrees("00:00:06")) or i2 > math.fabs(ephem.degrees("00:00:06")):
        print "intercepts: %s  %s" %(ephem.degrees(i1), ephem.degrees(i2))
        A = s2.getaz() - s1. getaz()
        print "A ist: %s oder %f" %(ephem.degrees(A), A)
        A1 = math.atan((i2-(i1*math.cos(A)))/(i1*math.sin(A)))
        print "A1 ist: %s oder %f" %(ephem.degrees(A1), A1)
        R = i1/(math.cos(A1))*(180*60/math.pi)
        print "R ist: %s oder %f" %(ephem.degrees(R), R)
        Az = s2.getaz() - A1
        print "azimut: %s" %ephem.degrees(Az)
        pos1 = deadRec(s1.getlon(), s1.getlat(), R, Az)
        pos2 = deadRec(s2.getlon(), s2.getlat(), R, Az)
        s1.setlon(pos1[0])
        s1.setlat(pos1[1])
        s2.setlon(pos2[0])
        s2.setlat(pos2[1])
        i2 = s1.getintercept()
        i1 = s2.getintercept()
        print "intercepts: %s  %s" %(ephem.degrees(i1), ephem.degrees(i2))
    return pos2       

def formlat(lat):
    lat = lat.znorm
    if lat >= 0:
        ns = "N"
    else:
        ns = "S"
    
    lat = ephem.degrees(math.fabs(lat))
    st = str(lat)
    sec = float(st[-4:])/60
    m = float(st[-7:-5])+sec
    d = st[:-8]            
    out = '%s°%.1f\'%s' %(d, m, ns)
    return out

def formlon(lon):
    lon = lon.znorm
    if lon >= 0:
        ns = "E"
    else:
        ns = "W"
    
    lon = ephem.degrees(math.fabs(lon))
    st = str(lon)
    sec = float(st[-4:])/60
    m = float(st[-7:-5])+sec
    d = st[:-8]            
    out = '%s°%.1f\'%s' %(d, m, ns)
    return out
    
    

## testcode
##
##drlon = ephem.degrees("10:30:00")
##drlat = ephem.degrees("40:30:00")
##alt1 = ephem.degrees("50:10:02.0")
##alt2 = ephem.degrees("51:20:51.7")
##s2 = Sight(drlon,drlat,"venus", alt1, "2012/7/15 6:00:00")
##s1 = Sight(drlon,drlat,"venus", alt2, "2012/7/15 11:00:00")
##pos = compfix(s1, s2)
##print "fixtest"
##print pos[0]
##print pos[1]



##
##lon = ephem.degrees("20:58.2")
##lat = ephem.degrees("70:1.7")
##hd = ephem.degrees("253:00:00")
##print "dr test"
##out=  deadRec(lon, lat, 30, hd)
##print out[0]
##print out[1]

