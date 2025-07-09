#! /usr/bin/env python
# -*- coding: koi8-r -*-

#
# opDate - date/time manipulation routines
# Some ideas came from Turbo Professional/Object Professional (t/o)pDate.PAS
#


from __future__ import print_function
from string import *
from time import *
from calendar import *
from opstring import *


MinYear = 1600
MaxYear = 3999
MinDate = 0x00000000 # = 01/01/1600
MaxDate = 0x000D6025 # = 12/31/3999
Date1900 = 0x0001AC05 # = 01/01/1900
Date1980 = 0x00021E28 # = 01/01/1980
Date2000 = 0x00023AB1 # = 01/01/2000
BadDate = 0x7FFFFFFF

Threshold2000 = 1900

MinTime = 0          # = 00:00:00 am
MaxTime = 86399      # = 23:59:59 pm
BadTime = 0x7FFFFFFF

SecondsInDay = 86400 # number of seconds in a day
SecondsInHour = 3600 # number of seconds in an hour
SecondsInMinute = 60 # number of seconds in a minute
HoursInDay = 24      # number of hours in a day
MinutesInHour = 60   # number of minutes in an hour

First2Months = 59    # 1600 was a leap year
FirstDayOfWeek = 5   # 01/01/1600 was a Saturday


# Errors
class opdate_error(Exception):
   pass


#
### Date manipulation routines
#

def IsLeapYear(Year):
   if ( (Year % 4 == 0) and (Year % 4000 != 0) and ((Year % 100 != 0) or (Year % 400 == 0)) ):
      return True
   return False


def _setYear(Year):
   # Internal function
   if Year < 100:
      Year = Year + 1900
      if Year < Threshold2000:
         Year = Year + 100
   return Year


def DaysInMonth(Month, Year):
   """ Return the number of days in the specified month of a given year """
   if Month in [1, 3, 5, 7, 8, 10, 12]:
      return 31

   elif Month in [4, 6, 9, 11]:
      return 30

   elif Month == 2:
      return 28+IsLeapYear(_setYear(Year))

   else:
      raise opdate_error("bad month `%s'" % str(Month))


def ValidDate(Day, Month, Year):
   """ Verify that day, month, year is a valid date """
   Year = _setYear(Year)

   if (Day < 1) or (Year < MinYear) or (Year > MaxYear):
      return False
   elif (Month >= 1) and (Month <= 12):
         return Day <= DaysInMonth(Month, Year)
   else:
      return False


def DMYtoDate(Day, Month, Year):
   """ Convert from day, month, year to a julian date """
   Year = _setYear(Year)

   if not ValidDate(Day, Month, Year):
      return BadDate

   if (Year == MinYear) and (Month < 3):
      if Month == 1:
         return Day-1
      else:
         return Day+30
   else:
      if Month > 2:
         Month = Month - 3
      else:
         Month = Month + 9
         Year = Year - 1
      Year = Year - MinYear

      return (((Year // 100)*146097) // 4) + (((Year % 100)*1461) // 4) + (((153*Month)+2) // 5)+Day+First2Months


def DateToDMY(Julian):
   """ Convert from a julian date to day, month, year """
   if Julian == BadDate:
      return 0, 0, 0

   if Julian <= First2Months:
      Year = MinYear
      if Julian <= 30:
         Month = 1
         Day = Julian + 1
      else:
         Month = 2
         Day = Julian-30
   else:
      I = (4*(Julian-First2Months))-1
      J = (4*((I % 146097) // 4))+3
      Year = (100*(I // 146097))+(J // 1461)
      I = (5*(((J % 1461)+4) // 4))-3
      Month = I // 153
      Day = ((I % 153)+5) // 5
      if Month < 10:
         Month = Month + 3
      else:
         Month = Month - 9
         Year = Year + 1
      Year = Year + MinYear

   return Day, Month, Year


def IncDate(Julian, Days, Months, Years):
   """ Add (or subtract) the number of months, days, and years to a date.
       Months and years are added before days. No overflow/underflow checks are made
   """
   Day, Month, Year = DateToDMY(Julian)
   Day28Delta = Day-28
   if Day28Delta < 0:
      Day28Delta = 0
   else:
      Day = 28

   Year = Year + Years
   Year = Year + Months // 12
   Month = Month + Months % 12
   if Month < 1:
      Month = Month + 12
      Year = Year - 1
   elif Month > 12:
      Month = Month - 12
      Year = Year + 1

   Julian = DMYtoDate(Day, Month, Year)
   if Julian != BadDate:
      Julian = Julian + Days + Day28Delta

   return Julian


def IncDateTrunc(Julian, Months, Years):
   """ Add (or subtract) the specified number of months and years to a date """
   Day, Month, Year = DateToDMY(Julian)
   Day28Delta = Day-28
   if Day28Delta < 0:
      Day28Delta = 0
   else:
      Day = 28

   Year = Year + Years
   Year = Year + Months // 12
   Month = Month + Months % 12
   if Month < 1:
      Month = Month + 12
      Year = Year - 1
   elif Month > 12:
      Month = Month - 12
      Year = Year + 1

   Julian = DMYtoDate(Day, Month, Year)
   if Julian != BadDate:
      MaxDay = DaysInMonth(Month, Year)
      if Day+Day28Delta > MaxDay:
         Julian = Julian + MaxDay-Day
      else:
         Julian = Julian + Day28Delta

   return Julian


def DateDiff(Date1, Date2):
   """ Return the difference in days,months,years between two valid julian dates """
   #we want Date2 > Date1
   if Date1 > Date2:
      _tmp = Date1
      Date1 = Date2
      Date2 = _tmp

   #convert dates to day,month,year
   Day1, Month1, Year1 = DateToDMY(Date1)
   Day2, Month2, Year2 = DateToDMY(Date2)

   #days first
   if Day2 < Day1:
      Month2 = Month2 - 1
      if Month2 == 0:
         Month2 = 12
         Year2 = Year2 - 1
      Day2 = Day2 + DaysInMonth(Month2, Year2)
   Days = abs(Day2-Day1)

   #now months and years
   if Month2 < Month1:
      Month2 = Month2 + 12
      Year2 = Year2 - 1
   Months = Month2-Month1
   Years = Year2-Year1

   return Days, Months, Years


def DayOfWeek(Julian):
   """ Return the day of the week for the date. Returns DayType(7) if Julian == BadDate. """
   if Julian == BadDate:
      raise opdate_error("bad date `%s'" % str(Julian))
   else:
      return (Julian+FirstDayOfWeek) % 7


def DayOfWeekDMY(Day, Month, Year):
   """ Return the day of the week for the day, month, year """
   return DayOfWeek( DMYtoDate(Day, Month, Year) )


#def MonthStringToMonth(MSt):
#   """ Convert the month name in MSt to a month (1..12) or -1 on error """
#   lmn = strptime.LongMonthNames[strptime.LANGUAGE]
#   smn = strptime.ShortMonthNames[strptime.LANGUAGE]
#   lmna = LongMonthNamesA
#
#   I = FindStr(MSt, lmn)+1 or FindStr(MSt, smn)+1 or \
#      FindStrUC(MSt, lmn)+1 or FindStrUC(MSt, smn)+1 or \
#      FindStr(MSt, lmna)+1 or FindStrUC(MSt, lmna)+1
#
#   return I-1


def Today():
   """ Returns today's date as a julian """
   Year, Month, Day = localtime(time())[0:3]
   return DMYtoDate(Day, Month, Year)

#
### Time manipulation routines
#

def TimeToHMS(T):
   """ Convert a Time variable to Hours, Minutes, Seconds """
   if T == BadTime:
      return 0, 0, 0

   else:
      Hours = T // SecondsInHour
      T = T - Hours*SecondsInHour
      Minutes = T // SecondsInMinute
      T = T - Minutes*SecondsInMinute
      Seconds = T

      return Hours, Minutes, Seconds


def HMStoTime(Hours, Minutes, Seconds):
   """ Convert Hours, Minutes, Seconds to a Time variable """
   Hours = Hours % HoursInDay
   T = Hours*SecondsInHour + Minutes*SecondsInMinute + Seconds

   return T % SecondsInDay


def ValidTime(Hours, Minutes, Seconds):
   """ Return true if Hours:Minutes:Seconds is a valid time """
   return (0 <= Hours < 24) and (0 <= Minutes < 60) and (0 <= Seconds < 60)


def CurrentTime():
   """ Returns current time in seconds since midnight """
   Hours, Minutes, Seconds = localtime(time())[3:6]
   return HMStoTime(Hours, Minutes, Seconds)


def TimeDiff(Time1, Time2):
   """ Return the difference in hours,minutes,seconds between two times """
   if Time1 > Time2:
      T = Time1-Time2
   else:
      T = Time2-Time1

   Hours, Minutes, Seconds = TimeToHMS(T)
   return Hours, Minutes, Seconds


def IncTime(T, Hours, Minutes, Seconds):
   """ Add the specified hours,minutes,seconds to T and return the result """
   T = T + HMStoTime(Hours, Minutes, Seconds)
   return T % SecondsInDay


def DecTime(T, Hours, Minutes, Seconds):
   """ Subtract the specified hours,minutes,seconds from T and return the result """
   Hours = Hours % HoursInDay
   T = T - HMStoTime(Hours, Minutes, Seconds)
   if T < 0:
      return T+SecondsInDay
   else:
      return T


def RoundToNearestHour(T, Truncate = False):
   """ Round T to the nearest hour, or Truncate minutes and seconds from T """
   Hours, Minutes, Seconds = TimeToHMS(T)
   Seconds = 0

   if not Truncate:
      if Minutes >= (MinutesInHour // 2):
         Hours = Hours + 1

   Minutes = 0
   return HMStoTime(Hours, Minutes, Seconds)


def RoundToNearestMinute(T, Truncate = False):
   """ Round T to the nearest minute, or Truncate seconds from T """
   Hours, Minutes, Seconds = TimeToHMS(T)

   if not Truncate:
      if Seconds >= (SecondsInMinute // 2):
         Minutes = Minutes + 1

   Seconds = 0
   return HMStoTime(Hours, Minutes, Seconds)


def DateTimeDiff(DT1, DT2):
   """ Return the difference in days,seconds between two points in time """
   # swap if DT1 later than DT2
   if (DT1[0] > DT2[0]) or ((DT1[0] == DT2[0]) and (DT1[1] > DT2[1])):
      _tmp = DT1
      DT1 = DT2
      DT2 = _tmp

   # the difference in days is easy
   Days = DT2[0]-DT1[0]

   # difference in seconds
   if DT2[1] < DT1[1]:
      # subtract one day, add 24 hours
      Days = Days - 1
      DT2[1] = DT2[1] + SecondsInDay

   Secs = DT2[1]-DT1[1]
   return Days, Secs


def IncDateTime(DT1, Days, Secs):
   """ Increment (or decrement) DT1 by the specified number of days and seconds
      and put the result in DT2 """
   DT2 = DT1[:]

   # date first
   DT2[0] = DT2[0] + Days

   if Secs < 0:
      # change the sign
      Secs = -Secs

      # adjust the date
      DT2[0] = DT2[0] - Secs // SecondsInDay
      Secs = Secs % SecondsInDay

      if Secs > DT2[1]:
         # subtract a day from DT2[0] and add a day's worth of seconds to DT2[1]
         DT2[0] = DT2[0] - 1
         DT2[1] = DT2[1] + SecondsInDay

      # now subtract the seconds
      DT2[1] = DT2[1] - Secs

   else:
      # increment the seconds
      DT2[1] = DT2[1] + Secs

      # adjust date if necessary
      DT2[0] = DT2[0] + DT2[1] // SecondsInDay

      # force time to 0..SecondsInDay-1 range
      DT2[1] = DT2[1] % SecondsInDay

   return DT2


#
### UTC (GMT) stuff
#

UTC_0Date = DMYtoDate(1, 1, 1970)


def DateTimeToGMT(Date, Time = False):
   Date = Date - UTC_0Date
   return Date*SecondsInDay + Time


def GMTtoDateTime(GMT):
   q, r = divmod(GMT, SecondsInDay)
   return q + UTC_0Date, r


#
### Cyrillic stuff
#

LongMonthNamesA = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
   'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря']


#
### Test stuff
#

def test():
   print("Is 1984 leap year?", IsLeapYear(1984))
   print("Is 1990 leap year?", IsLeapYear(1990))

   print("Days in month 8 year 1996:", DaysInMonth(8, 1996))

   print("Is date 8/12/1996 valid?", ValidDate(8, 12, 1996))
   print("Is date 40/11/1996 valid?", ValidDate(40, 11, 1996))
   print("Is date 8/14/1996 valid?", ValidDate(8, 14, 1996))

   print("Date->DMY for 138219:", DateToDMY(138219))

   diff = DateDiff(DMYtoDate(12, 10, 1996), DMYtoDate(12, 10, 1997))
   print("Date 12/10/1996 and date 12/10/1997 diff: %d years, %d months, %d days" % (diff[2], diff[1], diff[0]))

   diff = DateDiff(DMYtoDate(12, 10, 1996), DMYtoDate(12, 11, 1997))
   print("Date 12/10/1996 and date 12/11/1997 diff: %d years, %d months, %d days" % (diff[2], diff[1], diff[0]))

   diff = DateDiff(DMYtoDate(31, 1, 1996), DMYtoDate(1, 3, 1996))
   print("Date 31/01/1996 and date 01/03/1996 diff: %d years, %d months, %d days" % (diff[2], diff[1], diff[0]))


   #print("November is %dth month" % MonthStringToMonth("November"))

   print("Today is", Today())
   print("Now is", CurrentTime())

   print("My birthday 21 Dec 1967 is (must be Thursday):", day_name[DayOfWeekDMY(21, 12, 67)])

   gmt = DateTimeToGMT(DMYtoDate(21, 12, 1967), HMStoTime(23, 45, 0))
   # DOS version of gmtime has error processing dates before 1/1/1970 :(
   print("21 Dec 1967, 23:45:00 --", gmtime(gmt))
   D, T = GMTtoDateTime(gmt)
   print("(gmt) --", DateToDMY(D), TimeToHMS(T))

if __name__ == "__main__":
   test()
