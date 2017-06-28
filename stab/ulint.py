#!/usr/bin/python

import sys
import os
import math
ulIntPwr = sys.argv[1:]
ulIntPwr = map(lambda x: float(x), ulIntPwr)
weight = [0.794328235,0.897164117,1.129462706,1.421909302,1.790077754,2.253574373,2.837082046,3.571674683,4.496472021,5.660722891,11.07925268,27.82982449,69.90535853,175.5943216,441.0729938,630.9573445]


#print len(ulIntPwr), ulIntPwr
#print len(weight), weight

w_ulint = map(lambda x,y: x*y, weight, ulIntPwr)
NBIOT_NPusch_ULINT_fW = sum(w_ulint)/sum(ulIntPwr)
NBIOT_NPusch_ULINT_dBm = 10*math.log10(NBIOT_NPusch_ULINT_fW / 1000000000000)

print "ULINT: ", NBIOT_NPusch_ULINT_dBm
