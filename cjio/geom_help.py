import math

import numpy as np

MODULE_EARCUT_AVAILABLE = True
try:
    import mapbox_earcut
except ImportError as e:
    MODULE_EARCUT_AVAILABLE = False

def to_2d(p, n):
    #-- n must be normalised
    # p = np.array([1, 2, 3])
    # newell = np.array([1, 3, 4.2])
    # n = newell/math.sqrt(p[0]*p[0] + p[1]*p[1] + p[2]*p[2])
    x3 = np.array([1.1, 1.1, 1.1])    #-- is this always a good value??
    if (n == x3).all():
        x3 += np.array([1,2,3])
    x3 = x3 - np.dot(x3, n) * n
    # print(n, x3)
    x3 /= math.sqrt((x3**2).sum())   # make x a unit vector    
    y3 = np.cross(n, x3)
    return (np.dot(p, x3), np.dot(p, y3))


def get_normal_newell(poly):
    # find normal with Newell's method
    # print (poly)
    n = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    # if len(poly) == 0:
    #     print ("NOPOINTS")
    for i,p in enumerate(poly):
        ne = i + 1
        if (ne == len(poly)):
            ne = 0
        n[0] += ( (poly[i][1] - poly[ne][1]) * (poly[i][2] + poly[ne][2]) )
        n[1] += ( (poly[i][2] - poly[ne][2]) * (poly[i][0] + poly[ne][0]) )
        n[2] += ( (poly[i][0] - poly[ne][0]) * (poly[i][1] + poly[ne][1]) )
    
    if (n==np.array([0.0, 0.0, 0.0])).all():
        # print("one wrong")
        return (n, False)
    n = n / math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])    
    return (n, True)

def get_centroid(ring):
    from shapely.geometry.polygon import LinearRing
    from shapely.geometry.polygon import Point
    r = LinearRing(ring)
    c = r.representative_point()
    print("centroidddd:", r.contains(c))
    # print("centroidddd:", r.contains(Point(66, 11)))
    # return r.centroid
    return r.representative_point()

def triangulate_face(face, vnp):
    if not MODULE_EARCUT_AVAILABLE:
        raise ModuleNotFoundError("mapbox-earcut is not installed")
    if ((len(face) == 1) and (len(face[0]) == 3)):
        #        print ("Already a triangle")
        return face
    sf = np.array([], dtype=np.int32)
    for ring in face:
        sf = np.hstack((sf, np.array(ring)))
    sfv = vnp[sf]
    rings = np.zeros(len(face), dtype=np.int32)
    total = 0
    for i in range(len(face)):
        total += len(face[i])
        rings[i] = total
        # 1. normal with Newell's method
    n, b = get_normal_newell(sfv)
    sfv2d = np.zeros((sfv.shape[0], 2))
    for i, p in enumerate(sfv):
        xy = to_2d(p, n)
        sfv2d[i][0] = xy[0]
        sfv2d[i][1] = xy[1]
    result = mapbox_earcut.triangulate_float32(sfv2d, rings)

    for i, each in enumerate(result):
        result[i] = int(sf[each])

    #    print (type(result.reshape(-1, 3).tolist()[0][0]))
    return result.reshape(-1, 3).tolist()
