import json

from direct.showbase.ShowBase import ShowBase
from panda3d.core import PNMImage, LTexCoordd, LPoint2d, LPoint3d, LVector3d, \
    getDefaultCoordinateSystem, StaticTextFont
from panda3d.egg import EggData, EggTexture, EggGroup, EggVertexPool, EggPolygon, EggPoint, loadEggData


class Font:
    _coordinate_system = getDefaultCoordinateSystem()

    _pixels_per_unit = 16.0

    _vpool = None
    group = None

    def __init__(self, base: ShowBase, filename):
        self.base = base
        print(f"Opening font {filename}")
        font_data = json.load(open(filename))
        for provider in font_data["providers"]:

            if "ascii" not in provider["file"]:
                continue

            egg = EggData()

            self.group = EggGroup()
            egg.addChild(self.group)

            self._vpool = EggVertexPool("vpool")
            self.group.addChild(self._vpool)

            ds_group = EggGroup("ds")
            self.group.add_child(ds_group)
            vtx = self.make_vertex(LPoint2d(0.0, 32))
            point = EggPoint()
            ds_group.add_child(point)
            point.add_vertex(vtx)

            self.group.setSwitchFlag(True)
            self.group.setSwitchFps(2.0)

            self.texture = f"assets/textures/{provider["file"].replace("minecraft:", "")}"
            self.ascent = int(provider["ascent"])

            image = PNMImage(self.texture)
            eggTex = {}

            chars = provider["chars"]
            h, w = len(chars), len(chars[0])
            ch, cw = 1/h, 1/w
            ph, pw = image.getYSize()//h, image.getXSize()//w
            for y in range(h):
                for x in range(w):

                    char = ord(chars[y][x])
                    if char == 0:
                        continue

                    left = None
                    right = pw * (x+1) - 1
                    for px in range(pw * x, pw * (x+1)):
                        empty = True
                        for py in range(ph * y, ph * (y + 1)):
                            if image.getAlpha(px, py) > 0:
                                empty = False
                                if left is None:
                                    left = px
                                break
                        if empty:
                            if left is None:
                                continue
                            right = px - 1
                            break

                    if left is None:
                        left = pw * x
                        right = pw * x + 4

                    eggTex[char] = EggTexture(f"mc{char:03}", self.texture )
                    eggTex[char].setMinfilter(EggTexture.FTNearest)
                    eggTex[char].setMagfilter(EggTexture.FTNearest)
                    eggTex[char].setAnisotropicDegree(0)
                    eggTex[char].setQualityLevel(EggTexture.QLBest)
                    eggTex[char].setTransform2d((((right - left + 1) / pw) * cw, 0, 0,
                                                0, ch, 0,
                                                x * cw, 1 - (y + 1) * ch, 1))
                    egg.addChild(eggTex[char])

                    self.make_geom(h, 0, right - left + 1, ph, char, eggTex[char])

            self.font = StaticTextFont(loadEggData(egg))


    def make_vertex(self, xy: LPoint2d):
        """
        Allocates and returns a new vertex from the vertex pool representing the
        indicated 2-d coordinates.
        """
        return self._vpool.make_new_vertex(LPoint3d.origin(self._coordinate_system) +
                                      LVector3d.rfu(xy[0], 0.0, xy[1], self._coordinate_system))

    def make_geom(self, bitmap_top: int, bitmap_left: int, tex_x_size: float, tex_y_size: float, character: int, texture: EggTexture):
        """
        Generates the indicated character and adds it to the font description.
        """
        # Create an egg group to hold the polygon.
        group_name = str(character)
        group = EggGroup(group_name)
        self.group.add_child(group)

        if tex_x_size != 0 and tex_y_size != 0:
            # Determine the corners of the rectangle in geometric units.
            origin_y: float = bitmap_top / self._pixels_per_unit
            origin_x: float = bitmap_left / self._pixels_per_unit
            top: float = origin_y
            left: float = origin_x
            bottom: float = origin_y - tex_y_size / self._pixels_per_unit
            right: float = origin_x + tex_x_size / self._pixels_per_unit

            # And the corresponding corners in UV units.
            uv_top: float = 1.0
            uv_left: float = 0.0
            uv_bottom: float = 0.0
            uv_right: float = 1.0

            # Create the vertices for the polygon.
            v1 = self.make_vertex(LPoint2d(left, bottom))
            v2 = self.make_vertex(LPoint2d(right, bottom))
            v3 = self.make_vertex(LPoint2d(right, top))
            v4 = self.make_vertex(LPoint2d(left, top))

            v1.set_uv(LTexCoordd(uv_left, uv_bottom))
            v2.set_uv(LTexCoordd(uv_right, uv_bottom))
            v3.set_uv(LTexCoordd(uv_right, uv_top))
            v4.set_uv(LTexCoordd(uv_left, uv_top))

            poly = EggPolygon()
            group.addChild(poly)
            poly.addTexture(texture)

            poly.addVertex(v1)
            poly.addVertex(v2)
            poly.addVertex(v3)
            poly.addVertex(v4)

        # Now create a single point where the origin of the next character will be.
        v0 = self.make_vertex(LPoint2d(1.2 * tex_x_size / self._pixels_per_unit, 0.0))
        point = EggPoint()
        group.addChild(point)
        point.addVertex(v0)
