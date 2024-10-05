import json, random, os

from direct.directtools.DirectGeometry import LineNodePath
from direct.filter.FilterManager import FilterManager
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, WindowProperties, \
    CollisionNode, CollisionSegment, CollisionTraverser, CollisionHandlerQueue, \
    SamplerState, TransparencyAttrib, RenderState, CullFaceAttrib, ColorWriteAttrib, \
    ClockObject, TP_high, loadPrcFile, NodePath, PandaNode, Texture, Shader, AuxBitplaneAttrib, CollisionEntry, \
    LVector3f

from block import Block
from hud import Hud
from inventory import Inventory
from item import Item


class PyCraft(ShowBase):
    instance = None
    target_block = None
    target_face = None
    destroying = None
    destroy_ticks = 0
    destroyed_ticks = 0
    destroy_delay = 0
    ticks = 0

    WEST = LVector3f(1, 0, 0)
    EAST = LVector3f(-1, 0, 0)
    UP = LVector3f(0, 1, 0)
    DOWN = LVector3f(0, -1, 0)
    NORTH = LVector3f(0, 0, 1)
    SOUTH = LVector3f(0, 0, -1)

    def __init__(self):
        ShowBase.__init__(self)
        PyCraft.instance = self

        # Window setup
        wp = WindowProperties()
        wp.setTitle("PyCraft v0.1")
        wp.setCursorHidden(True)
        wp.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(wp)
        self.disableMouse()

        self.globalClock = ClockObject.getGlobalClock()

        # Lighting
        self.sun = DirectionalLight("sun")
        self.sun.getLens().setFilmSize(100, 100)
        self.sun.getLens().setNearFar(0.1, 20)
        self.sun.setShadowCaster(True, 4096, 4096)
        self.sun.setColorTemperature(7000)
        self.sun.color = self.sun.color * 2
        self.sun.setInitialState(RenderState.make(CullFaceAttrib.makeReverse(), ColorWriteAttrib.make(ColorWriteAttrib.COff)))
        self.sun.setCameraMask(Block.SHADOW_MASK)

        self.np_sun = self.render.attachNewNode(self.sun)

        self.np_sun.setPosHpr(0,0,10,35,-65,0)

        # Create depth offset for cheap soft shadows
        existentState = self.np_sun.node().getInitialState()
        tempNP = NodePath(PandaNode("temporary NP"))
        tempNP.setState(existentState)
        tempNP.setDepthWrite(True, 1)
        tempNP.setDepthOffset(2)
        self.np_sun.node().setInitialState(tempNP.getState())

        self.render.setLight(self.np_sun)


        skycol = Block.color_from_hex("#79A6FF")
        self.setBackgroundColor(skycol)

        self.ambient = AmbientLight("ambient")
        self.ambient.setColorTemperature(7000)
        self.ambient.color = self.ambient.color * 0.5
        np_ambient = self.render.attachNewNode(self.ambient)
        self.render.setLight(np_ambient)

        manager = FilterManager(self.win, self.cam)
        tex = Texture()
        dtex = Texture()
        ntex = Texture()
        quad = manager.renderSceneInto(colortex=tex, depthtex=dtex, auxtex=ntex, auxbits=AuxBitplaneAttrib.ABO_aux_normal)
        quad.setShader(Shader.load(Shader.SL_GLSL,
                                 vertex="shaders/post.vert",
                                 fragment="shaders/post.frag"))
        quad.setShaderInput("rendered", tex)
        quad.setShaderInput("depth", dtex)
        quad.setShaderInput("normal", ntex)

        # Targeting
        self.cTrav = CollisionTraverser("collisionTraverser")
        self.targetHandler = CollisionHandlerQueue()

        self.cam.setPos(0, 0, 0)
        picker_node = CollisionNode("gazeRay")
        picker_np = self.cam.attachNewNode(picker_node)
        picker_node.setFromCollideMask(Block.COLLIDE_MASK)
        self.target_ray = CollisionSegment(0, 0, 0, 0, 5.5, 0)
        picker_node.addSolid(self.target_ray)
        self.cTrav.addCollider(picker_np, self.targetHandler)

        # Controls
        self.mouse_sensitivity_x = 90
        self.mouse_sensitivity_y = 60
        self.walk_speed = 6
        self.strafe_speed = 6

        self.mouse_reset = True
        self.taskMgr.add(self.controls, "cam")

        self.__up_key = False
        self.__left_key = False
        self.__down_key = False
        self.__right_key = False
        self.__break_key = False
        self.__place_key = False

        self.accept("w", self.up_key, [True])
        self.accept("w-up", self.up_key, [False])
        self.accept("a", self.left_key, [True])
        self.accept("a-up", self.left_key, [False])
        self.accept("s", self.down_key, [True])
        self.accept("s-up", self.down_key, [False])
        self.accept("d", self.right_key, [True])
        self.accept("d-up", self.right_key, [False])
        self.accept("r", self.break_key, [True])
        self.accept("r-up", self.break_key, [False])
        self.accept("e", self.place_key, [True])
        self.accept("e-up", self.place_key, [False])
        self.accept("1", lambda s: self.hotbar(1) if s else None, [True])
        self.accept("2", lambda s: self.hotbar(2) if s else None, [True])
        self.accept("3", lambda s: self.hotbar(3) if s else None, [True])
        self.accept("4", lambda s: self.hotbar(4) if s else None, [True])
        self.accept("5", lambda s: self.hotbar(5) if s else None, [True])
        self.accept("6", lambda s: self.hotbar(6) if s else None, [True])
        self.accept("7", lambda s: self.hotbar(7) if s else None, [True])
        self.accept("8", lambda s: self.hotbar(8) if s else None, [True])
        self.accept("9", lambda s: self.hotbar(9) if s else None, [True])

        self.body = self.render.attachNewNode("body")
        self.cam.reparentTo(self.body)
        self.camLens.setFov(80)
        self.camLens.setNear(0.01)
        self.body.setPosHpr(0, -5, 2.5, 0, 0, 0)

        self.crosshair = OnscreenImage(image="assets/textures/gui/sprites/hud/crosshair.png", pos=(0, 0, 0), scale=(.15, 1, .15))
        self.crosshair.setImage(image="assets/textures/gui/sprites/hud/crosshair.png", transform=None)
        self.crosshair.setTransparency(TransparencyAttrib.MPremultipliedAlpha)
        self.crosshair.getTexture().setMagfilter(SamplerState.FT_nearest)
        self.crosshair.getTexture().setMinfilter(SamplerState.FT_nearest)

        self.hud = Hud(self)
        self.inventory = Inventory(self)

        self.aspect2d.setShaderAuto()

        blocks_data = json.load(open("data/blocks.json"))
        for block in blocks_data:
            Block.blocks_data[block["id"]] = block
            Block.blocks_data[block["name"]] = block
        items_data = json.load(open("data/items.json"))
        for item in items_data:
            Item.items_data[item["id"]] = item
            Item.items_data[item["name"]] = item

        # Generate world
        cols, rows, layers = 27, 27, 2
        self.blocks = [[[None for _ in range(cols)] for _ in range(layers)] for _ in range(rows)]
        self.block_colliders = {}
        for y in range(layers-1):
            for z in range(rows):
                for x in range(cols):
                    block_choice = random.choice([1,8,9,34,46,144,164,255])
                    block = Block.make(self, block_choice, x-13, y+random.choice([0,1]), z-13)
                    self.add_block(block)
                    self.block_colliders[block.collision_node] = block

        self.taskMgr.setupTaskChain("game", numThreads=1, threadPriority=TP_high)
        self.game_clock = ClockObject()
        self.game_clock.tick()
        self.game_task = self.taskMgr.add(self.game_update, "game_update", taskChain="game")


    def up_key(self, state):
        self.__up_key = state == True
    def left_key(self, state):
        self.__left_key = state == True
    def down_key(self, state):
        self.__down_key = state == True
    def right_key(self, state):
        self.__right_key = state == True
    def break_key(self, state):
        self.__break_key = state == True
    def place_key(self, state):
        self.__place_key = state == True

    def hotbar(self, slot):
        self.hud.select_slot(slot)

    def controls(self, task):
        delta = self.globalClock.getDt()

        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()

            if not self.mouse_reset:
                if not x == 0:
                    self.body.setH(self.body.getH() - x * self.mouse_sensitivity_x)

                if 90 > self.cam.getP() > -90:
                    self.cam.setP(self.cam.getP() + y * self.mouse_sensitivity_y)
                # If the camera is at a -90 or 90 degrees angle, this code helps it not get stuck.
                else:
                    if self.cam.getP() > 90:
                        self.cam.setP(self.cam.getP() - 1)
                    elif self.cam.getP() < -90:
                        self.cam.setP(self.cam.getP() + 1)

            self.mouse_reset = False

            self.win.movePointer(0, int(self.win.getProperties().getXSize() / 2),
                                 int(self.win.getProperties().getYSize() / 2))

        if self.__up_key:
            self.body.setY(self.body, self.walk_speed * delta)
        if self.__down_key:
            self.body.setY(self.body, -self.walk_speed * delta)

        if self.__left_key:
            self.body.setX(self.body, -self.strafe_speed * delta)
        if self.__right_key:
            self.body.setX(self.body, self.strafe_speed * delta)

        # Raycast target
        self.cTrav.traverse(self.render)
        if self.targetHandler.getNumEntries() > 0:
            self.targetHandler.sortEntries()
            entry: CollisionEntry = self.targetHandler.getEntry(0)
            target = entry.getIntoNodePath()
            if target in self.block_colliders:
                point = entry.getSurfacePoint(self.render) if entry.hasSurfacePoint() else None
                face = self.target_face
                if point is not None:
                    face = point - target.getPos(self.render)
                    x, y, z = abs(face.x), abs(face.y), abs(face.z)
                    face.x = (1 if face.x > 0 else -1) if x > z and x > y else 0
                    face.y = (1 if face.y > 0 else -1) if y > z and y > x else 0
                    face.z = (1 if face.z > 0 else -1) if z > x and z > y else 0
                if self.target_block != self.block_colliders[target] or self.target_face != face:
                    print(point, target.getPos(self.render), point - target.getPos(self.render), face)
                    self.target(self.block_colliders[target], face)
            else:
                self.target(None)
        else:
            self.target(None)

        if self.__break_key:
            if self.destroy_delay > 0:
                self.destroy_delay -= 1
            elif self.target_block and not self.destroying:
                self.destroy_block(self.target_block)
        elif self.destroying:
            self.destroy_block(None)

        return task.cont


    def destroy_block(self, target):
        if self.destroying == target:
            return

        if self.destroying:
            self.destroying.destroy_stage(-1)

        self.destroying = target
        self.destroy_ticks = 0 if target is None else target.destroy_ticks(1)
        self.destroyed_ticks = 0
        if target:
            target.destroy_stage(0)

    def target(self, target, face = None):
        self.target_face = face

        if target == self.target_block:
            return

        if self.destroying:
            self.destroy_block(target)

        if target:
            if self.target_block is not None:
                self.target_block.highlight(False)
            target.highlight(True)
        else:
            if self.target_block is not None:
                self.target_block.highlight(False)
        self.target_block = target

    def destroyed(self, block: Block):
        drops = block.data["drops"]
        if len(drops) > 0:
            item = Item.items_data[drops[0]] # TODO: figure out multiple drops
            self.inventory.add(item["name"], 1)
        if self.destroy_ticks > 1:
            self.destroy_block(None)
            self.destroy_delay = 6

    def add_block(self, block):
        self.blocks[block.x][block.y][block.z] = block

    def game_update(self, task):
        ftime = self.game_clock.getRealTime()
        if ftime < 0.05:
            return task.cont

        self.game_clock.setRealTime(ftime - 0.05)
        self.ticks += 1
        self.game_tick()

        return task.cont

    def game_tick(self):
        if self.destroying:
            self.destroyed_ticks += 1
            self.target_block.destroy_stage(self.destroyed_ticks / self.destroy_ticks)

loadPrcFile(os.path.dirname(os.path.abspath(__file__)) + "/Config.prc")
PyCraft().run()
