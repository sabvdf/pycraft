from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTriangles, Texture, Material, \
    RenderState, TextureAttrib, MaterialAttrib, GeomNode, NodePath, CollisionNode, CollisionBox, LPoint3


class Block():
    textures = {}
    material = None
    block_geoms = {}
    geom_states = {}
    def __init__(self, base, geom_type, texture, x, y, z):
        # Create geometry if needed
        if geom_type not in Block.block_geoms:
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

            Block.block_geoms[geom_type] = Geom(block_vdata)
            if geom_type == 1:
                # Creating primitive
                single_cube = GeomTriangles(Geom.UHStatic)
                # left
                single_cube.addVertices(2, 3, 4)
                single_cube.addVertices(2, 4, 5)
                # right
                single_cube.addVertices(6, 7, 8)
                single_cube.addVertices(6, 8, 9)
                # front
                single_cube.addVertices(10, 11, 12)
                single_cube.addVertices(10, 12, 13)
                # back
                single_cube.addVertices(14, 15, 16)
                single_cube.addVertices(14, 16, 17)
                # top
                single_cube.addVertices(18, 19, 20)
                single_cube.addVertices(18, 20, 21)
                # bottom
                single_cube.addVertices(22, 23, 24)
                single_cube.addVertices(22, 24, 25)
                single_cube.closePrimitive()

                Block.block_geoms[geom_type].addPrimitive(single_cube)

        # Load texture if not loaded yet
        if texture not in Block.textures:
            tex = Texture("Texture")
            tex.setup2dTexture()
            tex.read(f"textures/block/{texture}.png")
            tex.setMagfilter(Texture.FTNearest)
            tex.setMinfilter(Texture.FTNearest)
            Block.textures[texture] = TextureAttrib.make(tex)

        # Create default material if needed
        if Block.material == None:
            mat = Material("default")
            mat.set_shininess(5.0)
            mat.set_base_color((1, 1, 1, 1))
            Block.material = MaterialAttrib.make(mat)

        # Create new geom state
        if texture not in Block.geom_states:
            Block.geom_states[texture] = RenderState.make(Block.textures[texture], Block.material)

        # Create geom node
        geom_node = GeomNode(f"{texture}@{x},{y},{z}")
        geom_node.add_geom(Block.block_geoms[geom_type], Block.geom_states[texture])
        self.node_path = NodePath(geom_node)

        self.node_path.reparent_to(base.render)
        self.node_path.setScale(0.5, 0.5, 0.5)

        self.collision_node = self.node_path.attachNewNode(CollisionNode("collider"))
        self.collision_node.node().addSolid(CollisionBox(LPoint3(0, 0, 0), 1, 1, 1))

        self.x, self.y, self.z = x, y, z
        self.node_path.setPos(self.x, self.z, self.y)
