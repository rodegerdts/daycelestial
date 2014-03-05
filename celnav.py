# -*- coding: UTF-8 -*-

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
        elif self.target == "Mars":
            self.o = ephem.Mars()
            self.cordir = 0
        elif self.target == "Jupiter":
            self.o = ephem.Jupiter()
            self.cordir = 0
        elif self.target == "Saturn":
            self.o = ephem.Saturn()
            self.cordir = 0
        else:
            self.o = ephem.star(self.target)
            self.cordir = 0


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
##    print "timedif f:%f " %timediff
    distance = timediff*speed
##    print "distance: %f" %distance
    drpos = deadRec(s1.getlon(), s1.getlat(), distance, hdg)
##    print "drpos: %s   %s" %(drpos[0], drpos[1])
    s2.setlon(drpos[0])
    s2.setlat(drpos[1])
    i2 = s1.getintercept()
    i1 = s2.getintercept()
    while True:
##        print "intercepts: %s  %s" %(ephem.degrees(i1), ephem.degrees(i2))
        A = s2.getaz() - s1. getaz()
##        print "A ist: %s oder %f" %(ephem.degrees(A), A)
        A1 = math.atan((i2-(i1*math.cos(A)))/(i1*math.sin(A)))
##        print "A1 ist: %s oder %f" %(ephem.degrees(A1), A1)
        R = i1/(math.cos(A1))*(180*60/math.pi)
##        print "R ist: %s oder %f" %(ephem.degrees(R), R)
        Az = s2.getaz() - A1
##        print "azimut: %s" %ephem.degrees(Az)
        pos1 = deadRec(s1.getlon(), s1.getlat(), R, Az)
        pos2 = deadRec(s2.getlon(), s2.getlat(), R, Az)
        s1.setlon(pos1[0])
        s1.setlat(pos1[1])
        s2.setlon(pos2[0])
        s2.setlat(pos2[1])
        i2 = s1.getintercept()
        i1 = s2.getintercept()
        if math.fabs(i1) < math.fabs(ephem.degrees("00:00:06")) or math.fabs(i2) < math.fabs(ephem.degrees("00:00:06")):
        	break
##        print "intercepts: %s  %s" %(ephem.degrees(i1), ephem.degrees(i2))
    return pos2




def compmfix(s, speed=0, hdg=0):
    '''Compute a running fix from arbitary number of sights

    input is a list of sights, speed and heading.
    Uses least squares method as described in the nautical almanac.'''

    AA = 0
    BB = 0
    CC = 0
    DD = 0
    EE = 0
    FF = 0
    DO = 21

    sights = sorted(s, key=Sight.gettime)
    number = len(sights)

    Lon = sights[0].getlon()
    Lat = sights[0].getlat()

    while DO > 19:
        for i in sights:
            timediff = (i.gettime() - sights[0].gettime())*24
            ##print "timedif f:%f " %timediff
            distance = timediff*speed
            ##print "distance: %f" %distance
            drpos = deadRec(sights[0].getlon(), sights[0].getlat(), distance, hdg)
            ##print "drpos: %s   %s" %(drpos[0], drpos[1])
            i.setlon(drpos[0])
            i.setlat(drpos[1])
            P = i.getintercept()
            Z = i.getaz()

            AA = AA + ( math.cos( Z ) )**2
            BB = BB + math.cos( Z ) * math.sin( Z )
            CC = CC + ( math.sin( Z ) )**2
            DD = DD + P * math.cos( Z )
            EE = EE + P * math.sin( Z )
            FF = FF + P**2

        Lon = sights[0].getlon()
        Lat = sights[0].getlat()
        G = AA*CC-( BB )**2
        BI = Lat+(CC*DD-BB*EE)/G
        LI = Lon+(AA*EE-BB*DD)/(G*math.cos( Lat ))
        print DO
        ## calculate distance to DRpos
        DO = math.sqrt( ((LI-Lon)**2)*(( math.cos( Lat ))**2)+(BI-Lat)**2 )*60*180/math.pi
        sights[0].setlon(LI)
        sights[0].setlat(BI)

    ##calculate standart deviation
    S = FF - DD*(BI-Lat) - EE*(LI-Lon) * (math.cos( Lat ))
    StDev = math.sqrt(S/(number-2))*60*180/math.pi

    return [ephem.degrees(LI), ephem.degrees(BI), DO, StDev]







def nadeg(deg):
    '''format radiants to the format usually used in the nautical almanac.

    (ddd°mm.m')'''
    g = int(math.degrees(deg))
    m = (math.degrees(deg)-g)*60
    m = round(m,1)
    if m==60:    ##prevent rounding to 60 minutes
        m = 0
        g = g+1
    gm = "%s°%04.1f'" %(g,abs(m))
    return gm





def rad_dm(rad):
    '''format radiants to degrees and decimal minutes dd:mm.m

    excepts radiants og ephem degree as input'''
    g = int(math.degrees(rad))
    m = (math.degrees(rad)-g)*60
    m = round(m,1)
    if m==60:   ##prevent rounding to 60 minutes
        m = 0
        g = g+1
    dm = "%s:%04.1f" %(g,abs(m))
    return dm




def formlat(lat):
    '''format latitude to human readable format

    (ddd°mm.m' NS)'''
    lat = lat.znorm
    if lat >= 0:
        ns = "N"
    else:
        ns = "S"

    lat = nadeg(ephem.degrees(math.fabs(lat)))
    out = '%s%s' %(lat, ns)
    return out




def formlon(lon):
    '''forma longitude to human readable format

    (ddd°mm.m' EW)'''
    lon = lon.znorm
    if lon >= 0:
        ns = "E"
    else:
        ns = "W"

    lon = nadeg(ephem.degrees(math.fabs(lon)))

    out = '%s%s' %(lon, ns)
    return out



## testcode

# drlon = ephem.degrees("10:00:00")
# drlat = ephem.degrees("41:30:00")
# alt1 = ephem.degrees("50:10")
# alt2 = ephem.degrees("51:21")
# alt3 = ephem.degrees("48:38")
# alt4 = ephem.degrees("8:13")
# s2 = Sight(drlon,drlat,"venus", alt1, "2012/7/15 6:00:00")
# s1 = Sight(drlon,drlat,"venus", alt2, "2012/7/15 11:00:00")
# s3 = Sight(drlon,drlat,"Jupiter", alt3, "2012/7/15 11:00:00")
# s4 = Sight(drlon,drlat,"Mars", alt4, "2012/7/15 11:00:00")
##pos = compfix(s1, s2)
##print "fixtest"
##print formlon(pos[0])
##print formlat(pos[1])

# print "compmfix:"
# li=[s1,s2, s3, s4]
# pos = compmfix(li, 0, 0)
# print formlon(pos[0])
# print formlat(pos[1])
# print pos[2]
# print pos[3]




##
##lon = ephem.degrees("20:58.2")
##lat = ephem.degrees("70:1.7")
##hd = ephem.degrees("253:00:00")
##print "dr test"
##out=  deadRec(lon, lat, 30, hd)
##print out[0]
##print out[1]
