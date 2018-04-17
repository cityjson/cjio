
import os
import json
import jsonschema
import jsonref
import urlparse


def dict_raise_on_duplicates(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           raise ValueError("Invalid CityJSON file, duplicate key for City Object IDs: %r" % (k))
        else:
           d[k] = v
    return d


def validate_cityjson(j):
    isValid = True
    #-- fetch proper schema
    if j["version"] == "0.6":
        schema = 'schemas/v06/cityjson.json'
    elif j["version"] == "0.5":
        schema = 'schemas/cityjson-v05.schema.json'
    else:
        return False
    #-- open the schema
    fins = open(schema)
    jtmp = json.loads(fins.read())
    fins.seek(0)
    if "$id" in jtmp:
        u = urlparse.urlparse(jtmp['$id'])
        os.path.dirname(u.path)
        base_uri = u.scheme + "://" + u.netloc + os.path.dirname(u.path) + "/" 
    else:
        abs_path = os.path.abspath(os.path.dirname(schema))
        base_uri = 'file://{}/'.format(abs_path)
    js = jsonref.loads(fins.read(), jsonschema=True, base_uri=base_uri)
    #-- load the schema for the cityobjects.json
    sco_path = os.path.abspath(os.path.dirname(schema))
    sco_path += '/cityobjects.json'
    jsco = json.loads(open(sco_path).read())
    #-- validate the file against the schema
    try:
        jsonschema.validate(j, js)
    except jsonschema.ValidationError as e:
        # print ("ERROR:   ", e.message)
        raise Exception(e.message)
        return False
    except jsonschema.SchemaError as e:
        # print ("ERROR:   ", e)
        raise Exception(e.message)
        return False
    return isValid