
import numpy as np
from math import sqrt

def to_2d(p, n):
    #-- n must be normalised
    # p = np.array([1, 2, 3])
    # newell = np.array([1, 3, 4.2])
    # n = newell/sqrt(p[0]*p[0] + p[1]*p[1] + p[2]*p[2])
    x3 = np.array([1.1, 1.1, 1.1])    #-- is this always a good value??
    if((n==x3).all()):
        x3 += np.array([1,2,3])
    x3 = x3 - np.dot(x3, n) * n
    # print(n, x3)
    x3 /= sqrt((x3**2).sum())   # make x a unit vector    
    y3 = np.cross(n, x3)
    return (np.dot(p, x3), np.dot(p, y3))


def get_normal_newell(poly):
    # find normal with Newell's method
    # print (poly)
    n = np.array([0.0, 0.0, 0.0])
    # if len(poly) == 0:
    #     print ("NOPOINTS")
    for i,p in enumerate(poly):
        ne = i + 1
        if (ne == len(poly)):
            ne = 0
        n[0] += ( (poly[i][1] - poly[ne][1]) * (poly[i][2] + poly[ne][2]) )
        n[1] += ( (poly[i][2] - poly[ne][2]) * (poly[i][0] + poly[ne][0]) )
        n[2] += ( (poly[i][0] - poly[ne][0]) * (poly[i][1] + poly[ne][1]) )
    
    # if (n==np.array([0.0, 0.0, 0.0])).all():
    #     print ("oh collapsed triangle:", poly)
       
    n = n / sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])    
    return n