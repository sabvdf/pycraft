from math import sin, cos, pi

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomTriangles, GeomVertexWriter, GeomNode, Texture, \
    TextureAttrib, NodePath, RenderState, ModelRoot, Mat4, DirectionalLight, Material, MaterialAttrib, AmbientLight


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Creating vertex data.
        block_vdata = GeomVertexData('cube', GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
        block_vdata.setNumRows(3)

        vertex = GeomVertexWriter(block_vdata, 'vertex')
        normal = GeomVertexWriter(block_vdata, 'normal')
        texcoord = GeomVertexWriter(block_vdata, 'texcoord')

        vertex.addData3(0, 0, 0)
        vertex.addData3(0, 0, 0)
        texcoord.addData2(0, 0)
        texcoord.addData2(0, 0)
        normal.addData3(0, 0, 0)
        normal.addData3(0, 0, 0)

        # left
        vertex.addData3(-1, 1, -1)
        vertex.addData3(-1, -1, -1)
        vertex.addData3(-1, -1, 1)
        vertex.addData3(-1, 1, 1)
        texcoord.addData2(0, 0)
        texcoord.addData2(1, 0)
        texcoord.addData2(1, 1)
        texcoord.addData2(0, 1)
        normal.addData3(-1, 0, 0)
        normal.addData3(-1, 0, 0)
        normal.addData3(-1, 0, 0)
        normal.addData3(-1, 0, 0)

        # right
        vertex.addData3(1, -1, -1)
        vertex.addData3(1, 1, -1)
        vertex.addData3(1, 1, 1)
        vertex.addData3(1, -1, 1)
        texcoord.addData2(0, 0)
        texcoord.addData2(1, 0)
        texcoord.addData2(1, 1)
        texcoord.addData2(0, 1)
        normal.addData3(1, 0, 0)
        normal.addData3(1, 0, 0)
        normal.addData3(1, 0, 0)
        normal.addData3(1, 0, 0)

        # front
        vertex.addData3(-1, -1, -1)
        vertex.addData3(1, -1, -1)
        vertex.addData3(1, -1, 1)
        vertex.addData3(-1, -1, 1)
        texcoord.addData2(0, 0)
        texcoord.addData2(1, 0)
        texcoord.addData2(1, 1)
        texcoord.addData2(0, 1)
        normal.addData3(0, -1, 0)
        normal.addData3(0, -1, 0)
        normal.addData3(0, -1, 0)
        normal.addData3(0, -1, 0)

        # back
        vertex.addData3(1, 1, -1)
        vertex.addData3(-1, 1, -1)
        vertex.addData3(-1, 1, 1)
        vertex.addData3(1, 1, 1)
        texcoord.addData2(0, 0)
        texcoord.addData2(1, 0)
        texcoord.addData2(1, 1)
        texcoord.addData2(0, 1)
        normal.addData3(0, 1, 0)
        normal.addData3(0, 1, 0)
        normal.addData3(0, 1, 0)
        normal.addData3(0, 1, 0)

        # top
        vertex.addData3(-1, -1, 1)
        vertex.addData3(1, -1, 1)
        vertex.addData3(1, 1, 1)
        vertex.addData3(-1, 1, 1)
        texcoord.addData2(0, 0)
        texcoord.addData2(1, 0)
        texcoord.addData2(1, 1)
        texcoord.addData2(0, 1)
        normal.addData3(0, 0, 1)
        normal.addData3(0, 0, 1)
        normal.addData3(0, 0, 1)
        normal.addData3(0, 0, 1)

        # bottom
        vertex.addData3(-1, 1, -1)
        vertex.addData3(1, 1, -1)
        vertex.addData3(1, -1, -1)
        vertex.addData3(-1, -1, -1)
        texcoord.addData2(0, 0)
        texcoord.addData2(1, 0)
        texcoord.addData2(1, 1)
        texcoord.addData2(0, 1)
        normal.addData3(0, 0, -1)
        normal.addData3(0, 0, -1)
        normal.addData3(0, 0, -1)
        normal.addData3(0, 0, -1)

        # Creating primitive - a.
        block_prim = GeomTriangles(Geom.UHStatic)
        # left
        block_prim.addVertices(2, 3, 4)
        block_prim.addVertices(2, 4, 5)
        # right
        block_prim.addVertices(6, 7, 8)
        block_prim.addVertices(6, 8, 9)
        # front
        block_prim.addVertices(10, 11, 12)
        block_prim.addVertices(10, 12, 13)
        # back
        block_prim.addVertices(14, 15, 16)
        block_prim.addVertices(14, 16, 17)
        # top
        block_prim.addVertices(18, 19, 20)
        block_prim.addVertices(18, 20, 21)
        # bottom
        block_prim.addVertices(22, 23, 24)
        block_prim.addVertices(22, 24, 25)
        block_prim.closePrimitive()

        block_geom = Geom(block_vdata)
        block_geom.addPrimitive(block_prim)

        # Load texture.
        cobblestone_tex = Texture("Texture")
        cobblestone_tex.setup2dTexture()
        cobblestone_tex.read("textures/block/cobblestone.png")
        cobblestone_tex.setMagfilter(Texture.FTNearest)
        cobblestone_tex.setMinfilter(Texture.FTNearest)

        # Create new material.
        mat = Material("cobblestone")
        mat.set_shininess(5.0)
        mat.set_base_color((1, 1, 1, 1))

        # Create new geom state.
        cobblestone_state = RenderState.make(TextureAttrib.make(cobblestone_tex), MaterialAttrib.make(mat))

        # Create geom node.
        for b in range(125):
            geom_node = GeomNode(f"Block{b:04}")
            geom_node.add_geom(block_geom, cobblestone_state)
            root = NodePath(geom_node)

            root.reparent_to(self.render)
            root.setScale(0.5, 0.5, 0.5)
            root.setPos((b//25)-2.5, (b//5%5)-2.5, (b%5)-2.5)


        # Create light.
        sun = DirectionalLight("sun")
        sun.getLens().set_film_size(10)
        sun.getLens().set_near_far(0.1, 17)
        sun.set_color((1, 1, 1, 1))
        sun.set_shadow_caster(True, 1024, 1024)

        np_sun = NodePath(sun)
        np_sun.setPosHpr(2,2,10,15,-65,0)
        np_sun.reparent_to(self.render)
        self.render.set_light(np_sun)

        ambient = AmbientLight("ambient")
        ambient.setColor((0.5, 0.5, 0.5, 1))
        np_ambient = self.render.attachNewNode(ambient)
        self.render.setLight(np_ambient)

        self.render.set_shader_auto()

        self.camera.setPos(-10, -10, 5)
        self.camera.setHpr(-45, -20, 0)
        mat = Mat4(self.camera.getMat())
        mat.invertInPlace()
        self.mouseInterfaceNode.setMat(mat)

app = MyApp()
app.run()
