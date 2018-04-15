

def print_info(j):
    #-- CityJSON version
    print "CityJSON version: ", j["version"] 

    #-- CityObjects
    print "===== CityObjects ====="
    print "Total : ", len(j["CityObjects"])

    d = set()
    for id in j["CityObjects"]:
        d.add(j['CityObjects'][id]['type'])
    print "Types:" 
    for each in d:
        print "\t", each
    d.clear()
    for id in j["CityObjects"]:
        for geom in j['CityObjects'][id]['geometry']:
            d.add(geom["type"])
    print "Geometries present:"
    for each in d:
        print "\t", each


    #-- metadata
    print "===== Metadata =====" 
    if "metadata" not in j:
        print "  none" 
    else:
        for each in j["metadata"]:
            if each == 'crs':
                print "  crs: EPSG:", j["metadata"]["crs"]["epsg"]
            else:
                print " ", each

    #--  vertices
    print "===== Vertices ====="
    print "Total:", len(j["vertices"])

    #-- appearance
    print "===== Appearance ====="
    if 'appearance' not in j:
        print "  none"
    else:
        if 'textures' in j['appearance']:
            print "  textures:", len(j['appearance']['textures'])
        if 'materials' in j['appearance']:
            print "  materials:", len(j['appearance']['materials'])