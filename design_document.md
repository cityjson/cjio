API for the data model

Allows to work with city models in a script. The API follows the data model, thus each CityObject type has its own class, children and parents.

## Data prep

Return an iterator over each City Object type. Only 1st-level objects. If the requested type is not in the city model, the iterator is empty.

The getters are named exactly after the City Object types.
```python
cm = cjio.load("some_model.json")
cm.building()
cm.bridge()
cm.cityobjectgroup()
cm.cityfurniture()
cm.genericcityobject()
cm.landuse()
cm.plantcover()
cm.railway()
cm.road()
cm.solitaryvegetationobject()
cm.tinrelief()
cm.transportsquare()
cm.tunnel()
cm.waterbody()
```

Using a single getter function, and pass the type as argument. It should get both 1st-level and 2nd-level city objects. But in case of 2nd-level objects, how do we keep the reference to the parents?
```python
cm = cjio.load("some_model.json")
cm.get_cityobjects("building")
cm.get_cityobjects("buildingpart")
```

Or for instance, sth like this should get the roof geometry of a building, provided that surfaces have semantics.

```python
cm = cjio.load("some_model.json")
building_1 = cm.building.get(1)
roof_geom = building_1.roofsurface.geometry
```

Get footprints, wall, roofs from LoD1 AND LoD2

How to work with a 3d model and its pointcloud?

## ML Features

How do we operate with 3D geometry? Do we cast to something from some library that has 3D geom? Or just provide getters for the vertices?

Python libraries with 3D geoms:

+ http://www.open3d.org/docs/python_api/open3d.geometry.Geometry3D.html#open3d.geometry.Geometry3D


Compute the volume of a building.

```python
cm = cjio.load("some_model.json")
for building in cm.get_cityobjects("building"):
    if building.children is None:
        # so, what exactly does this geometry object contain?
        geometry = building.get_geometry()        
        # or just dump all the vertices of the geometry
        vertices = building.get_vertices()
```

Get shape descriptors from the footrpints

Compute roof overhang as a distance between footprint and roofprint

Compute roof levels and roof types

(compare model to point cloud)

**!!! the most important software feature here is to allow the users to easily integrate their own cityobject/geometry processing functions with cjio !!!**

## Export

Save cityobject attributes in tabular format (eg. tsv)

Save cityobject attributes in pandas dataframe

## ML

Use the tabular output as input for scikit-learn (or any library). One can use `feather` to transport the objects to R.


