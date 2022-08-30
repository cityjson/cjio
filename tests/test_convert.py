from cjio import convert


class TestGltf:

    def test_convert_to_glb(self, delft):
        glb = convert.to_glb(delft.j)


class TestB3dm:

    def test_convert_to_b3dm(self, delft):
        glb = convert.to_glb(delft.j)
        b3dm = convert.to_b3dm(delft, glb)
