import glob
from cjio import cityjson

to_upgrade_to = "1.1"

for f in glob.glob("./**/*.json", recursive=True):
    # print(f)
    cj_file = open(f, "r")
    cm = cityjson.reader(file=cj_file)
    if cm.get_version() != to_upgrade_to:
        print(f)
        cm.upgrade_version(to_upgrade_to, 3)
        cityjson.save(cm, f)
    # re = cm.validate()
    # print(re)
    # print(cm)
    # break
