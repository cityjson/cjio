API for the data model

Allows to work with city models in a script. The API follows the data model, thus each CityObject type has its own class, children and parents.

## Data prep

### CityObject types

A cityobject with children.

```json
"CityObjects": {
  "id-1": {
    "type": "Building",
    "geographicalExtent": [ 84710.1, 446846.0, -5.3, 84757.1, 446944.0, 40.9 ], 
    "attributes": { 
      "measuredHeight": 22.3,
      "roofType": "gable",
      "owner": "Elvis Presley"
    },
    "children": ["id-2"],
    "geometry": [{...}]
  },
  "id-2": {
    "type": "BuildingPart", 
    "parents": ["id-1"],
    "children": ["id-3"],
    ...
  },
  "id-3": {
    "type": "BuildingInstallation", 
    "parents": ["id-2"],
    ...
  },
  "id-4": {
    "type": "LandUse", 
    ...
  }
}
```

Using a single getter function, and pass the type as argument. It should get both 1st-level and 2nd-level city objects. But in case of 2nd-level objects, how do we keep the reference to the parents?
```python
def get_cityobjects(type):
    """Return a generator over the CityObjects of the given type. Type can be 1st-level or 2nd-level CityObject."""
    if type is None:
        yield all cityobjects
    else:
        yield cityobjects of the given type

def get_children():
    if cityobject has children:
        yield list of children
    else:
        yield list()

def get_parents():
    if cityobject has parents:
        yield list of parents
    else:
        yield list()

cm = cjio.load("some_model.json")
buildings = cm.get_cityobjects("building")
for building in buildings:
    children = building.get_children()

buildingparts = cm.get_cityobjects("buildingpart")
for part in buildingparts:
    part.get_children()
    part.get_parents()
```

Or for instance, sth like this should get the roof geometry of a building, provided that surfaces have semantics.

```python
cm = cjio.load("some_model.json")
building_1 = cm.building.get(1)
roof_geom = building_1.roofsurface.geometry
```

Get footprints, wall, roofs from LoD1 AND LoD2

How to work with a 3d model and its pointcloud?

### Working with semantics

```python
class Geometry:
    def __init__(self, co):
        self.lod = co['geometry']['lod']
        self.type = co['geometry']['type']
        self.boundaries = self._get_boundary(co)
        # also need to handle surface semantics here somewhere
        self.semantics = self._get_semantics(co)
    
    def _get_geometry(self, co):
        loop through co['geometry']['boundaries'] and get the vertex coordinates
        return geometry sf style
        
    def _get_semantics(self, co):
        """Return a set of semantic surfaces that the CityObject has"""
        return set([sem['type'] for sem in co['geometry']['semantics']['surfaces']])

class SemanticSurface(Geometry):
    def __init__(self):
        self.type = "RoofSurface"
        self.children = list()
        self.parent = int()
        self.attributes = dict()
        self.boundaries = self._get_geometry() 
    
    def _get_geometry(self):
        """Get the geometry of the surface"""
        # this might duplicate the geometry, because the full geometry is already exists, dereferenced in the parent Geometry object
        extract the related parts of the CityObject geometry


cm = cjio.load("some_model.json")
for building in cm.get_cityobjects("building"):
    # so, what exactly does this geometry object contain? For now, we only return the Geometry object from JSON as it is. The same as cm['CityObjects'][0]['geometry']. Later we can think about converting the json to something.
    geometry = building.get_geometry()
    isinstance(geometry, Geometry)
    geometry.lod
    geometry.type
    geometry.boundaries # I think we should return the boundaries simple feature style, verticies included. It makes it much easier to operate on it.    
    # or just dump all the vertices of the geometry as [(x,y,z),(x,y,z),...]
    vertices = building.get_vertices()
    
    roofs = building.get_surface('roofsurface')
    walls = building.get_surface('wallsurface')
    grounds = building.get_surface('groundsurface')
    for roof in roofs:
        children = roof.get_children()
```

## ML Features

How do we operate with 3D geometry? Do we cast to something from some library that has 3D geom? Or just provide getters for the vertices?

Python libraries with 3D geoms:

+ http://www.open3d.org/docs/python_api/open3d.geometry.Geometry3D.html#open3d.geometry.Geometry3D


### Compute the volume of a building.

```python
class Geometry:
    def __init__(self, co):
        self.lod = co['geometry']['lod']
        self.type = co['geometry']['type']
        self.boundaries = self._get_boundary(co)
    
    def _get_geometry(self, co):
        loop through co['geometry']['boundaries'] and get the vertex coordinates
        return geometry sf style

def compute_volume(geometry):
    if geometry.boundaries is empty:
        return 0
    if geometry.lod < 2:
        figure out what surface is what
    else:
        use the surface semantics 
    if geometry.type == 'Solid':
        compute the volume
    elif geometry.type == 'Point':
        raise TypeError("Cannot compute the volume of Point geometry")
    return volume

cm = cjio.load("some_model.json")
for building in cm.get_cityobjects("building"):
    geometry = building.get_geometry()
    volume_parent = compute_volume(geometry)
    
    for child in building.get_children():
    # actually, we need to do this recursively in order to visit the children of children too, because it is
    # not defined how many level deep we need to go
        geometry = child.get_geometry()
        volume_child = compute_volume(geometry)
        
    volume = volume_parent + volume_child
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


