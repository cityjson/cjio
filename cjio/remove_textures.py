
import json


def remove_textures(j):
    if "appearance" in j:
        if "textures" in j["appearance"]:
            del j["appearance"]["textures"]
        if "vertices-texture" in j["appearance"]:
            del j["appearance"]["vertices-texture"]
        if "default-theme-texture" in j["appearance"]:
            del j["appearance"]["default-theme-texture"]

