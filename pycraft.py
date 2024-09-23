import json
import random

from direct.directtools.DirectGeometry import LineNodePath
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, WindowProperties, \
    Vec4, CollisionNode, CollisionSegment, CollisionTraverser, CollisionHandlerQueue, \
    SamplerState, TransparencyAttrib, VBase3, RenderState, \
    CullFaceAttrib, ColorWriteAttrib, ClockObject, loadPrcFileData, TP_high

from block import Block
from tool import Tool


class PyCraft(ShowBase):
    target_block = None
    destroying = None
    destroy_ticks = 0
    destroyed_ticks = 0
    ticks = 0

    def __init__(self):
        ShowBase.__init__(self)

        # Window setup
        wp = WindowProperties()
        wp.setTitle("PyCraft v0.1")
        wp.setCursorHidden(True)
        wp.setMouseMode(WindowProperties.M_confined)
        wp.setSize(1024, 600)
        self.win.requestProperties(wp)
        self.disableMouse()

        self.globalClock = ClockObject.getGlobalClock()

        loadPrcFileData("", "lock-to-one-cpu 0")
        loadPrcFileData("", "support-threads 1")

        # Lighting
        self.sun = DirectionalLight("sun")
        self.sun.getLens().setFilmSize(100)
        self.sun.getLens().setNearFar(0.1, 20)
        # self.sun.set_shadow_caster(True, 4096, 4096)
        self.sun.setColorTemperature(8000)
        self.sun.color = self.sun.color * 4
        self.sun.setInitialState(RenderState.make(CullFaceAttrib.makeReverse(), ColorWriteAttrib.make(ColorWriteAttrib.COff)))

        self.np_sun = self.render.attachNewNode(self.sun)
        self.np_sun.setPosHpr(2,2,10,15,-65,0)
        self.render.setLight(self.np_sun)

        skycol = VBase3(0x79 / 255.0, 0xA6 / 255.0, 0xFF / 255.0)
        self.setBackgroundColor(skycol)

        self.ambient = AmbientLight("ambient")
        self.ambient.setColorTemperature(8000)
        self.ambient.color = self.ambient.color * 0.4
        np_ambient = self.render.attachNewNode(self.ambient)
        self.render.setLight(np_ambient)

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

        # Targeted block highlight
        self.highlight = LineNodePath(self.render, colorVec=Vec4(0, 0, 0, 1))
        self.highlight.setThickness(5)
        self.highlight.drawLines([((-0.502, -0.502, -0.502), (-0.502, 0.502, -0.502))])
        self.highlight.drawLines([((-0.502, 0.502, -0.502), (0.502, 0.502, -0.502))])
        self.highlight.drawLines([((0.502, 0.502, -0.502), (0.502, -0.502, -0.502))])
        self.highlight.drawLines([((0.502, -0.502, -0.502), (-0.502, -0.502, -0.502))])

        self.highlight.drawLines([((-0.502, -0.502, -0.502), (-0.502, -0.502, 0.502))])
        self.highlight.drawLines([((-0.502, 0.502, -0.502), (-0.502, 0.502, 0.502))])
        self.highlight.drawLines([((0.502, 0.502, -0.502), (0.502, 0.502, 0.502))])
        self.highlight.drawLines([((0.502, -0.502, -0.502), (0.502, -0.502, 0.502))])

        self.highlight.drawLines([((-0.502, -0.502, 0.502), (-0.502, 0.502, 0.502))])
        self.highlight.drawLines([((-0.502, 0.502, 0.502), (0.502, 0.502, 0.502))])
        self.highlight.drawLines([((0.502, 0.502, 0.502), (0.502, -0.502, 0.502))])
        self.highlight.drawLines([((0.502, -0.502, 0.502), (-0.502, -0.502, 0.502))])
        self.highlight.create()
        self.highlight.reparentTo(self.render)
        self.highlight.setPos(0,0,0)
        self.highlight.setShaderOff()

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

        self.body = self.render.attachNewNode("body")
        self.cam.reparentTo(self.body)
        self.camLens.setFov(80)
        self.camLens.setNear(0.01)
        self.body.setPosHpr(0, -5, 2.5, 0, 0, 0)

        self.crosshair = OnscreenImage(image="textures/gui/sprites/hud/crosshair.png", pos=(0, 0, 0), scale=(.15, 1, .15))
        self.crosshair.setImage(image="textures/gui/sprites/hud/crosshair.png", transform=None)
        self.crosshair.setTransparency(TransparencyAttrib.MPremultipliedAlpha)
        self.crosshair.getTexture().setMagfilter(SamplerState.FT_nearest)
        self.crosshair.getTexture().setMinfilter(SamplerState.FT_nearest)

        blocks_data = json.load(open("blocks.json"))

        # Generate world
        cols, rows, layers = 27, 27, 2
        self.blocks = [[[None for _ in range(cols)] for _ in range(layers)] for _ in range(rows)]
        self.block_colliders = {}
        for y in range(layers-1):
            for z in range(rows):
                for x in range(cols):
                    block_data = blocks_data[random.choice([1,8,9,34,46,144,164,255])]
                    textures = []
                    block_model = json.load(open(f"models/block/{block_data["name"]}.json"))
                    block = Block.make(self, block_data, block_model, x-13, y+random.choice([0,1]), z-13)
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
            target = self.targetHandler.getEntry(0).getIntoNodePath()
            if target in self.block_colliders:
                if self.target_block != self.block_colliders[target]:
                    self.target(self.block_colliders[target])
            else:
                self.target(None)
        else:
            self.target(None)

        if self.__break_key:
            if self.target_block and not self.destroying:
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

    def target(self, target):
        if target == self.target_block:
            return

        if self.destroying:
            self.destroy_block(target)

        if target:
            self.highlight.setPos(target.node_path.getPos())
            self.highlight.show()
        else:
            self.highlight.hide()
        self.target_block = target

    def destroyed(self, block):
        print(f"{block} destroyed!")

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

PyCraft().run()
