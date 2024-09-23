import math

from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTriangles, Texture, Material, \
    RenderState, TextureAttrib, MaterialAttrib, GeomNode, NodePath, CollisionNode, CollisionBox, LPoint3, TextureStage, \
    BitMask32

from tool import Tool


class Block:
    SINGLE_CUBE = 1
    ONLY_SIDES = 2
    TOP_BOTTOM = 3
    ALL_DIFFERENT = 4

    COLLIDE_MASK = BitMask32(0x10)
    textures = {}
    materials = {}
    block_geoms = {}
    geom_states = {}
    destroy = []
    destroyed_stage = -1

    @staticmethod
    def make(base, block_data, block_model, x, y, z):
        textures = []
        tints = []
        texture_data = block_model["textures"]
        match block_model["parent"]:
            case "minecraft:block/cube_all":
                geom_type = Block.SINGLE_CUBE
                textures.append(texture_data["all"])
                if "elements" in block_model:
                    tints.append(block_model["elements"][0]["faces"]["top"].get("tintindex", None))
            case "minecraft:block/cube_column":
                geom_type = Block.ONLY_SIDES
                textures.append(texture_data["side"])
                textures.append(texture_data["end"])
                if "elements" in block_model:
                    tints.append(block_model["elements"][0]["faces"]["north"].get("tintindex", None))
                    tints.append(block_model["elements"][0]["faces"]["top"].get("tintindex", None))
            case "minecraft:block/cube_column_horizontal":
                geom_type = Block.ONLY_SIDES
                textures.append(texture_data["side"])
                textures.append(texture_data["end"])
                if "elements" in block_model:
                    tints.append(block_model["elements"][0]["faces"]["north"].get("tintindex", None))
                    tints.append(block_model["elements"][0]["faces"]["up"].get("tintindex", None))
            case _:
                if texture_data["top"] and texture_data["bottom"] and texture_data["side"]:
                    geom_type = Block.TOP_BOTTOM
                    textures.append(texture_data["side"])
                    textures.append(texture_data["top"])
                    textures.append(texture_data["bottom"])
                    if "elements" in block_model:
                        tints.append(block_model["elements"][0]["faces"]["north"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["up"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["down"].get("tintindex", None))
                else:
                    geom_type = Block.ALL_DIFFERENT
                    textures.append(texture_data["west"])
                    textures.append(texture_data["east"])
                    textures.append(texture_data["south"])
                    textures.append(texture_data["north"])
                    textures.append(texture_data["top"])
                    textures.append(texture_data["bottom"])
                    if "elements" in block_model:
                        tints.append(block_model["elements"][0]["faces"]["west"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["east"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["south"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["north"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["up"].get("tintindex", None))
                        tints.append(block_model["elements"][0]["faces"]["down"].get("tintindex", None))
        return Block(base, geom_type, block_data["name"], textures, tints, block_data["hardness"], [Tool.TYPE_SHOVEL], Tool.NO_TOOL, x, y, z)

    def __init__(self, base, geom_type, name, textures, tints, hardness, best_tools, minimum_tool, x, y, z):
        self.__name = name
        # Create geometry if needed
        if geom_type not in Block.block_geoms:
            # Creating vertex data.
            block_vdata = GeomVertexData("cube", GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
            block_vdata.setNumRows(3)

            vertex = GeomVertexWriter(block_vdata, "vertex")
            normal = GeomVertexWriter(block_vdata, "normal")
            texcoord = GeomVertexWriter(block_vdata, "texcoord")

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

            Block.block_geoms[geom_type] = []
            match geom_type:
                case Block.SINGLE_CUBE:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
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

                    Block.block_geoms[geom_type][0].addPrimitive(single_cube)

                case Block.ONLY_SIDES:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    # Creating primitive
                    sides = GeomTriangles(Geom.UHStatic)
                    # left
                    sides.addVertices(2, 3, 4)
                    sides.addVertices(2, 4, 5)
                    # right
                    sides.addVertices(6, 7, 8)
                    sides.addVertices(6, 8, 9)
                    # front
                    sides.addVertices(10, 11, 12)
                    sides.addVertices(10, 12, 13)
                    # back
                    sides.addVertices(14, 15, 16)
                    sides.addVertices(14, 16, 17)
                    sides.closePrimitive()
                    Block.block_geoms[geom_type][0].addPrimitive(sides)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    top_bottom = GeomTriangles(Geom.UHStatic)
                    # top
                    top_bottom.addVertices(18, 19, 20)
                    top_bottom.addVertices(18, 20, 21)
                    # bottom
                    top_bottom.addVertices(22, 23, 24)
                    top_bottom.addVertices(22, 24, 25)
                    top_bottom.closePrimitive()
                    Block.block_geoms[geom_type][1].addPrimitive(top_bottom)

                case Block.TOP_BOTTOM:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    # Creating primitive
                    sides = GeomTriangles(Geom.UHStatic)
                    # left
                    sides.addVertices(2, 3, 4)
                    sides.addVertices(2, 4, 5)
                    # right
                    sides.addVertices(6, 7, 8)
                    sides.addVertices(6, 8, 9)
                    # front
                    sides.addVertices(10, 11, 12)
                    sides.addVertices(10, 12, 13)
                    # back
                    sides.addVertices(14, 15, 16)
                    sides.addVertices(14, 16, 17)
                    sides.closePrimitive()
                    Block.block_geoms[geom_type][0].addPrimitive(sides)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    top = GeomTriangles(Geom.UHStatic)
                    # top
                    top.addVertices(18, 19, 20)
                    top.addVertices(18, 20, 21)
                    top.closePrimitive()
                    Block.block_geoms[geom_type][1].addPrimitive(top)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    bottom = GeomTriangles(Geom.UHStatic)
                    # bottom
                    bottom.addVertices(22, 23, 24)
                    bottom.addVertices(22, 24, 25)
                    bottom.closePrimitive()
                    Block.block_geoms[geom_type][2].addPrimitive(bottom)

                case Block.ALL_DIFFERENT:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    # Creating primitive
                    left = GeomTriangles(Geom.UHStatic)
                    # left
                    left.addVertices(2, 3, 4)
                    left.addVertices(2, 4, 5)
                    left.closePrimitive()
                    Block.block_geoms[geom_type][0].addPrimitive(left)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    right = GeomTriangles(Geom.UHStatic)
                    # right
                    right.addVertices(6, 7, 8)
                    right.addVertices(6, 8, 9)
                    right.closePrimitive()
                    Block.block_geoms[geom_type][1].addPrimitive(right)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    front = GeomTriangles(Geom.UHStatic)
                    # front
                    front.addVertices(10, 11, 12)
                    front.addVertices(10, 12, 13)
                    front.closePrimitive()
                    Block.block_geoms[geom_type][2].addPrimitive(front)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    back = GeomTriangles(Geom.UHStatic)
                    # back
                    back.addVertices(14, 15, 16)
                    back.addVertices(14, 16, 17)
                    back.closePrimitive()
                    Block.block_geoms[geom_type][3].addPrimitive(back)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    top = GeomTriangles(Geom.UHStatic)
                    # top
                    top.addVertices(18, 19, 20)
                    top.addVertices(18, 20, 21)
                    top.closePrimitive()
                    Block.block_geoms[geom_type][4].addPrimitive(top)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    bottom = GeomTriangles(Geom.UHStatic)
                    # bottom
                    bottom.addVertices(22, 23, 24)
                    bottom.addVertices(22, 24, 25)
                    bottom.closePrimitive()
                    Block.block_geoms[geom_type][5].addPrimitive(bottom)

        # Load texture if not loaded yet
        if self.__name not in Block.textures:
            Block.textures[self.__name] = []
            for texture in textures:
                Block.textures[self.__name].append(self.get_texture(texture))

        # Create geometry node
        geom_node = GeomNode(f"{self.__name}@{x},{y},{z}")
        # Create new geometry state if needed
        for t in range(len(textures)):
            texture = textures[t]
            tint = tints[t] if len(tints) > t else ""
            geom_index = f"{texture}{tint}"
            if geom_index not in Block.geom_states:
                Block.geom_states[geom_index] = RenderState.make(Block.textures[self.__name][t], self.get_material(tint))
            geom_node.addGeom(Block.block_geoms[geom_type][t], Block.geom_states[geom_index])
        self.node_path = NodePath(geom_node)

        # Load destroy stage textures if needed
        if not Block.destroy:
            for i in range(10):
                Block.destroy.append(Texture("Texture"))
                Block.destroy[i].setup2dTexture()
                Block.destroy[i].read(f"textures/block/destroy_stage_{i}.png")
                Block.destroy[i].setMagfilter(Texture.FTNearest)
                Block.destroy[i].setMinfilter(Texture.FTNearest)
        self.destroy_ts = TextureStage("destroy")
        self.destroy_ts.setCombineRgb(TextureStage.CMModulate,
            TextureStage.CSPrevious, TextureStage.COSrcColor, TextureStage.CSTexture, TextureStage.COOneMinusSrcColor)

        self.node_path.reparentTo(base.render)
        self.node_path.setScale(0.5, 0.5, 0.5)

        self.collision_node = self.node_path.attachNewNode(CollisionNode("collider"))
        self.collision_node.node().addSolid(CollisionBox(LPoint3(0, 0, 0), 1, 1, 1))
        self.collision_node.setCollideMask(Block.COLLIDE_MASK)

        self.x, self.y, self.z = x, y, z
        self.node_path.setPos(self.x, self.z, self.y)

        self.__base = base
        self.__hardness = hardness
        self.__best_tools = best_tools
        self.__minimum_tool = minimum_tool

    def __str__(self):
        return f"{self.__name} @ {self.x},{self.y},{self.z}"

    def get_material(self, tint):
        try:
            tint_index = int(tint)
        except (TypeError, ValueError):
            tint_index = None
        if tint_index not in Block.materials:
            mat = Material("default")
            mat.setShininess(5.0)
            match tint_index:
                case 0:
                    mat.setBaseColor((0, 1, 0, 1))
                case _:
                    mat.setBaseColor((1, 1, 1, 1))
            Block.materials[tint_index] = MaterialAttrib.make(mat)
        return Block.materials[tint_index]

    @staticmethod
    def get_texture(texture):
        tex = Texture("Texture")
        tex.setup2dTexture()
        tex.read(f"textures/{texture}.png".replace("minecraft:",""))
        tex.setMagfilter(Texture.FTNearest)
        tex.setMinfilter(Texture.FTNearest)
        return TextureAttrib.make(tex)

    def destroy_ticks(self, tool_type = Tool.NO_TOOL, on_ground = True, in_water = False, tool_material = Tool.NO_TOOL, efficiency_level = 0,
                      haste_level = 0, mining_fatigue_level = 0, has_aqua_affinity = False):
        speed_multiplier = 1
        can_harvest = tool_material < self.__minimum_tool

        match tool_material:
            case Tool.MATERIAL_WOOD:
                tool_multiplier = 2
            case Tool.MATERIAL_STONE:
                tool_multiplier = 2
            case Tool.MATERIAL_IRON:
                tool_multiplier = 2
            case Tool.MATERIAL_DIAMOND:
                tool_multiplier = 2
            case Tool.MATERIAL_NETHERITE:
                tool_multiplier = 2
            case Tool.MATERIAL_GOLD:
                tool_multiplier = 2
            case _:
                tool_multiplier = 1
        if tool_type in self.__best_tools:
            speed_multiplier = tool_multiplier
            if can_harvest:
                speed_multiplier = 1
            elif efficiency_level > 0:
                speed_multiplier += efficiency_level ** 2 + 1

        if haste_level > 0:
            speed_multiplier *= 0.2 * haste_level + 1

        if mining_fatigue_level > 0:
            speed_multiplier *= 0.3 ** min(mining_fatigue_level, 4)

        if in_water and not has_aqua_affinity:
            speed_multiplier /= 5

        if not on_ground:
            speed_multiplier /= 5

        damage = speed_multiplier / self.__hardness

        if can_harvest:
            damage /= 30
        else:
            damage /= 100

        # Instant breaking
        if (damage > 1):
            return 0

        ticks = math.ceil(1 / damage)
        return ticks

    def destroy_stage(self, amount):
        stage = int(amount * 10.0)
        if self.destroyed_stage != stage:
            self.destroyed_stage = stage
            if 0 <= stage <= 9:
                self.node_path.setTexture(self.destroy_ts, Block.destroy[stage])
            elif stage > 9:
                self.__base.destroyed(self)
                self.node_path.detachNode()
            else:
                self.node_path.clearTexture(self.destroy_ts)
