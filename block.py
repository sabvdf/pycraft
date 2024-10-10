import json
import math

from direct.task.TaskManagerGlobal import taskMgr
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTriangles, \
    Texture, Material, RenderState, TextureAttrib, MaterialAttrib, GeomNode, NodePath, \
    CollisionNode, CollisionBox, LPoint3, TextureStage, BitMask32, LColor, PandaNode, Shader, GraphicsBuffer, \
    SamplerState, LVector3f

from hud import Hud
from tool import Tool


class Block:
    SINGLE_CUBE = 1
    ONLY_SIDES = 2
    TOP_BOTTOM = 3
    ALL_DIFFERENT = 4

    WEST = 1
    EAST = 2
    NORTH = 3
    SOUTH = 4
    UP = 5
    DOWN = 6

    SHADOW_MASK = BitMask32(0x010)
    COLLIDE_MASK = BitMask32(0x100)
    __shader = None

    blocks_data = {}

    textures = {}
    materials = {}
    block_geoms = {}
    geom_states = {}
    block_icons = {}
    highlight_tex = None
    destroy = []
    destroyed_stage = -1

    @staticmethod
    def make(base, name_or_id, x, y, z):
        parts = []
        textures = []
        tints = []
        overlays = []
        block_data = Block.blocks_data[name_or_id]
        block_model = json.load(open(f"assets/models/block/{block_data["name"]}.json"))
        texture_data = block_model["textures"]
        match block_model["parent"]:
            case "minecraft:block/cube_all":
                geom_type = Block.SINGLE_CUBE
                parts.append(("all", "top"))
            case "minecraft:block/cube_column":
                geom_type = Block.ONLY_SIDES
                parts.append(("side", "north"))
                parts.append(("end", "up"))
            case "minecraft:block/cube_column_horizontal":
                geom_type = Block.ONLY_SIDES
                parts.append(("side", "north"))
                parts.append(("end", "up"))
            case _:
                if texture_data["top"] and texture_data["bottom"] and texture_data["side"]:
                    geom_type = Block.TOP_BOTTOM
                    parts.append(("side", "north"))
                    parts.append(("top", "up"))
                    parts.append(("bottom", "down"))
                else:
                    geom_type = Block.ALL_DIFFERENT
                    parts.append(("west", "west"))
                    parts.append(("east", "east"))
                    parts.append(("south", "south"))
                    parts.append(("north", "north"))
                    parts.append(("top", "up"))
                    parts.append(("bottom", "down"))

        for (texture_side, face_side) in parts:
            if "elements" in block_model:
                textures.append(texture_data[block_model["elements"][0]["faces"][face_side].get("texture").replace("#", "")])
                tints.append(block_model["elements"][0]["faces"][face_side].get("tintindex", None))
                if len(block_model["elements"]) > 1 and face_side in block_model["elements"][1]["faces"]:
                    overlays.append((texture_data[block_model["elements"][1]["faces"][face_side].get("texture").replace("#", "")], block_model["elements"][1]["faces"][face_side].get("tintindex", None)))
                else:
                    overlays.append((None, None))
            else:
                textures.append(texture_data[texture_side])
                overlays.append((None, None))

        return Block(base, geom_type, block_data, block_model, parts, textures, overlays, tints, [Tool.TYPE_SHOVEL], Tool.NO_TOOL, x, y, z)

    def __init__(self, base, geom_type, block_data, block_model, parts, textures, overlays, tints, best_tools, minimum_tool, x, y, z):
        self.data = block_data
        self.model = block_model
        self._name = block_data["name"]
        # Load shader if needed
        if Block.__shader is None:
            Block.__shader = Shader.load(Shader.SL_GLSL,
                                 vertex="shaders/lighting.vert",
                                 fragment="shaders/lighting.frag")

        # Create geometry if needed
        if geom_type not in Block.block_geoms:
            # Creating vertex data.
            block_vdata = GeomVertexData("cube", GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
            block_vdata.setNumRows(3)

            vertex = GeomVertexWriter(block_vdata, "vertex")
            normal = GeomVertexWriter(block_vdata, "normal")
            texcoord = GeomVertexWriter(block_vdata, "texcoord")

            # padding data (why is this needed?)
            vertex.addData3(0, 0, 0)
            vertex.addData3(0, 0, 0)
            vertex.addData3(0, 0, 0)
            vertex.addData3(0, 0, 0)
            texcoord.addData2(0, 0)
            texcoord.addData2(0, 0)
            texcoord.addData2(0, 0)
            texcoord.addData2(0, 0)
            normal.addData3(0, 0, 0)
            normal.addData3(0, 0, 0)
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
                    single_cube = Block.make_primitive([Block.WEST, Block.EAST, Block.NORTH, Block.SOUTH, Block.UP, Block.DOWN])
                    Block.block_geoms[geom_type][0].addPrimitive(single_cube)

                case Block.ONLY_SIDES:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    sides = Block.make_primitive([Block.WEST, Block.EAST, Block.NORTH, Block.SOUTH])
                    Block.block_geoms[geom_type][0].addPrimitive(sides)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    top_bottom = Block.make_primitive([Block.UP, Block.DOWN])
                    Block.block_geoms[geom_type][1].addPrimitive(top_bottom)

                case Block.TOP_BOTTOM:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    sides = Block.make_primitive([Block.WEST, Block.EAST, Block.NORTH, Block.SOUTH])
                    Block.block_geoms[geom_type][0].addPrimitive(sides)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    top = Block.make_primitive([Block.UP])
                    Block.block_geoms[geom_type][1].addPrimitive(top)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    bottom = Block.make_primitive([Block.DOWN])
                    Block.block_geoms[geom_type][2].addPrimitive(bottom)

                case Block.ALL_DIFFERENT:
                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    left = Block.make_primitive([Block.WEST])
                    Block.block_geoms[geom_type][0].addPrimitive(left)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    right = Block.make_primitive([Block.EAST])
                    Block.block_geoms[geom_type][1].addPrimitive(right)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    front = Block.make_primitive([Block.SOUTH])
                    Block.block_geoms[geom_type][2].addPrimitive(front)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    back = Block.make_primitive([Block.NORTH])
                    Block.block_geoms[geom_type][3].addPrimitive(back)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    top = Block.make_primitive([Block.UP])
                    Block.block_geoms[geom_type][4].addPrimitive(top)

                    Block.block_geoms[geom_type].append(Geom(block_vdata))
                    bottom = Block.make_primitive([Block.DOWN])
                    Block.block_geoms[geom_type][5].addPrimitive(bottom)

        # Load texture if not loaded yet
        if self._name not in Block.textures:
            Block.textures[self._name] = []
            for texture in textures:
                Block.textures[self._name].append(self.get_texture(texture))

        # Create root node
        block_node = PandaNode(f"{self._name}@{x},{y},{z}")
        self.node_path = NodePath(block_node)
        # Create geometry nodes
        self.geom_paths = []
        for p in range(len(parts)):
            geom_node = GeomNode(f"{parts[p]}")
            texture = textures[p]
            tint = tints[p] if len(tints) > p else ""
            geom_index = f"{texture}{tint}"
            if geom_index not in Block.geom_states:
                Block.geom_states[geom_index] = RenderState.make(Block.textures[self._name][p], MaterialAttrib.make(Material("default")))
            geom_node.addGeom(Block.block_geoms[geom_type][p], Block.geom_states[geom_index])
            geom_np = NodePath(geom_node)
            geom_np.reparentTo(self.node_path)

            geom_np.setShader(Block.__shader)

            tint_color = Block.get_tint_color(tint)
            if tint_color:
                geom_np.setColorScale(tint_color)
            (overlay_texture, overlay_tint) = overlays[p]
            geom_np.setShaderInput("overlay", 0 if overlay_texture is None else 1)
            geom_np.setShaderInput("overlayColor", (1, 1, 1, 1) if overlay_tint is None else Block.get_tint_color(overlay_tint))
            if overlay_texture is not None:
                overlay_tex = Block.get_texture(overlay_texture, False)
                overlay_ts = TextureStage("overlay")
                overlay_ts.setSort(1)
                overlay_ts.setMode(TextureStage.MDecal)
                geom_np.setTexture(overlay_ts, overlay_tex)
            geom_np.setShaderInput("destroy", 0)
            geom_np.setShaderInput("highlight", 0)
            self.geom_paths.append(geom_np)

        # Load highlight texture if needed
        if not Block.highlight_tex:
            Block.highlight_tex = Texture("Texture")
            Block.highlight_tex.setup2dTexture()
            Block.highlight_tex.read(f"assets/textures/block/highlight.png")
            Block.highlight_tex.setMagfilter(Texture.FTNearest)
            Block.highlight_tex.setMinfilter(Texture.FTNearest)
        self.highlight_ts = TextureStage("highlight")
        self.highlight_ts.setSort(2)
        self.highlight_ts.setCombineRgb(TextureStage.CMModulate,
            TextureStage.CSPrevious, TextureStage.COSrcColor, TextureStage.CSTexture, TextureStage.COOneMinusSrcColor)
        self.node_path.setTexture(self.highlight_ts, Block.highlight_tex)

        # Load destroy stage textures if needed
        if not Block.destroy:
            for i in range(10):
                Block.destroy.append(Texture("Texture"))
                Block.destroy[i].setup2dTexture()
                Block.destroy[i].read(f"assets/textures/block/destroy_stage_{i}.png")
                Block.destroy[i].setMagfilter(Texture.FTNearest)
                Block.destroy[i].setMinfilter(Texture.FTNearest)
        self.destroy_ts = TextureStage("destroy")
        self.destroy_ts.setSort(3)
        self.destroy_ts.setCombineRgb(TextureStage.CMModulate,
            TextureStage.CSPrevious, TextureStage.COSrcColor, TextureStage.CSTexture, TextureStage.COOneMinusSrcColor)

        cnode = CollisionNode("collider")
        self.collision_node = self.node_path.attachNewNode(cnode)
        self.collision_node.node().addSolid(CollisionBox(LPoint3(0, 0, 0), .98, .98, .98))
        self.collision_node.setCollideMask(Block.COLLIDE_MASK)

        self.rigidbody = BulletRigidBodyNode()
        self.rigidbody.addShape(BulletBoxShape(LVector3f(0.49, 0.49, 0.49)))

        if isinstance(base, NodePath):
            self.body = base.attachNewNode(self.rigidbody)
        else:
            self.body = base.render.attachNewNode(self.rigidbody)

        self.node_path.reparentTo(self.body)
        self.node_path.setScale(0.5, 0.5, 0.5)
        self.node_path.showThrough(Block.SHADOW_MASK)

        self.x, self.y, self.z = x, y, z
        self.body.setPos(self.x, self.z, self.y)

        self.__base = base
        self.__hardness = block_data["hardness"]
        self.__best_tools = best_tools
        self.__minimum_tool = minimum_tool

    def __str__(self):
        return f"{self._name} @ {self.x},{self.y},{self.z}"

    @staticmethod
    def make_primitive(sides):
        primitive = GeomTriangles(Geom.UHStatic)
        for side in sides:
            offset = 4 * side
            primitive.addVertices(offset + 0, offset + 1, offset + 2)
            primitive.addVertices(offset + 0, offset + 2, offset + 3)
        primitive.closePrimitive()
        return primitive

    @staticmethod
    def set_icon_on(component, name):
        if name in Block.block_icons:
            if Block.block_icons[name] is not None:
                if component is not None:
                    component.setTexture(Block.block_icons[name])
            return

        def defer_icon(component, name):
            hud = Hud.instance

            Block.block_icons[name] = None
            test_copy = Block.make(hud.block_scene, name, 0, 0, 0)


            tex = Texture(f"{name}_item")
            tex.setFormat(Texture.F_srgb_alpha)
            tex.setMagfilter(SamplerState.FT_nearest)
            tex.setMinfilter(SamplerState.FT_nearest)
            hud.block_buffer.clearRenderTextures()
            hud.block_buffer.addRenderTexture(tex, GraphicsBuffer.RTMBindOrCopy)
            hud.block_buffer.setActive(True)
            hud._base.graphicsEngine.renderFrame()

            def set_result(component, name, test_copy):
                test_copy.node_path.removeNode()
                hud.block_buffer.setActive(False)

                Block.block_icons[name] = tex
                if component is not None:
                    component.setTexture(tex)

            taskMgr.doMethodLater(0, set_result, f"grab {name} icon", (component, name, test_copy))
        taskMgr.doMethodLater(0, defer_icon, f"make {name} icon", (component, name))

    @staticmethod
    def get_texture(texture, attrib = True):
        tex = Texture("Texture")
        tex.setup2dTexture()
        tex.read(f"assets/textures/{texture}.png".replace("minecraft:",""))
        tex.setMagfilter(Texture.FTNearest)
        tex.setMinfilter(Texture.FTNearest)
        if attrib:
            return TextureAttrib.make(tex)
        else:
            return tex

    @staticmethod
    def get_tint_color(tint):
        try:
            tint_index = int(tint)
        except (TypeError, ValueError):
            tint_index = None
        match tint_index:
            case 0:
                return Block.color_from_hex("#79C05A")
        return LColor(1, 1, 1, 1)

    @staticmethod
    def color_from_hex(hex, factor = 1):
        hex = hex.lstrip('#')
        match len(hex):
            case 8:
                return LColor(tuple(int(hex[i:i + 2], 16) / 255.0 / factor for i in (0, 2, 4)) + (int(hex[6:8], 16) / 255.0,))
            case 6:
                return LColor(tuple(int(hex[i:i + 2], 16) / 255.0 / factor for i in (0, 2, 4)) + (1,))
        return LColor(1, 0, 1, 1)

    def highlight(self, on):
        for path in self.geom_paths:
            path.setShaderInput("highlight", 1 if on else 0)

    def destroy_ticks(self, tool_type = Tool.NO_TOOL, on_ground = True, in_water = False, tool_material = Tool.NO_TOOL, efficiency_level = 0,
                      haste_level = 0, mining_fatigue_level = 0, has_aqua_affinity = False):
        speed_multiplier = 1
        can_harvest = tool_material <= self.__minimum_tool

        match tool_material:
            case Tool.MATERIAL_WOOD:
                tool_multiplier = 2
            case Tool.MATERIAL_STONE:
                tool_multiplier = 4
            case Tool.MATERIAL_IRON:
                tool_multiplier = 6
            case Tool.MATERIAL_DIAMOND:
                tool_multiplier = 8
            case Tool.MATERIAL_NETHERITE:
                tool_multiplier = 9
            case Tool.MATERIAL_GOLD:
                tool_multiplier = 12
            case _:
                tool_multiplier = 1
        if tool_type in self.__best_tools:
            speed_multiplier = tool_multiplier
            if not can_harvest:
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
                for path in self.geom_paths:
                    path.setShaderInput("destroy", 1)
            elif stage > 9:
                self.__base.destroyed(self)
                self.node_path.detachNode()
            else:
                self.node_path.clearTexture(self.destroy_ts)
                for path in self.geom_paths:
                    path.setShaderInput("destroy", 0)
