import random

from direct.directtools.DirectGeometry import LineNodePath
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import GeomNode, DirectionalLight, AmbientLight, WindowProperties, \
    Vec4, CollisionNode, CollisionSegment, CollisionTraverser, CollisionHandlerQueue, \
    SamplerState, TransparencyAttrib, VBase3, VBase4, BoundingVolume, RenderState, \
    CullFaceAttrib, ColorWriteAttrib

from block import Block

class PyCraft(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Window setup
        wp = WindowProperties()
        wp.setTitle("PyCraft v0.1")
        wp.setCursorHidden(True)
        wp.setMouseMode(WindowProperties.MConfined)
        wp.setSize(1024, 600)
        self.win.requestProperties(wp)
        self.disableMouse()

        # Lighting
        self.sun = DirectionalLight("sun")
        self.sun.getLens().set_film_size(100)
        self.sun.getLens().set_near_far(0.1, 20)
        # self.sun.set_shadow_caster(True, 4096, 4096)
        self.sun.set_color_temperature(8000)
        self.sun.color = self.sun.color * 4
        self.sun.setInitialState(RenderState.make(CullFaceAttrib.makeReverse(), ColorWriteAttrib.make(ColorWriteAttrib.COff)))

        self.np_sun = self.render.attach_new_node(self.sun)
        self.np_sun.setPosHpr(2,2,10,15,-65,0)
        self.render.set_light(self.np_sun)

        skycol = VBase3(0x79 / 255.0, 0xA6 / 255.0, 0xFF / 255.0)
        self.set_background_color(skycol)

        self.ambient = AmbientLight("ambient")
        self.ambient.set_color_temperature(8000)
        self.ambient.color = self.ambient.color * 0.4
        np_ambient = self.render.attach_new_node(self.ambient)
        self.render.set_light(np_ambient)

        # Targeting
        self.cTrav = CollisionTraverser('collisionTraverser')
        self.targetHandler = CollisionHandlerQueue()

        self.cam.setPos(0, 0, 0)
        pickerNode = CollisionNode('gazeRay')
        pickerNP = self.cam.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.targetRay = CollisionSegment(0, 0, 0, 0, 5.5, 0)
        pickerNode.addSolid(self.targetRay)
        self.cTrav.addCollider(pickerNP, self.targetHandler)

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
        self.taskMgr.add(self.camControl, "cam")

        self.__upKey = False
        self.__leftKey = False
        self.__downKey = False
        self.__rightKey = False
        self.__breakKey = False
        self.__placeKey = False

        self.accept("w", self.upKey, [True])
        self.accept("w-up", self.upKey, [False])
        self.accept("a", self.leftKey, [True])
        self.accept("a-up", self.leftKey, [False])
        self.accept("s", self.downKey, [True])
        self.accept("s-up", self.downKey, [False])
        self.accept("d", self.rightKey, [True])
        self.accept("d-up", self.rightKey, [False])
        self.accept("r", self.breakKey, [True])
        self.accept("r-up", self.breakKey, [False])
        self.accept("e", self.placeKey, [True])
        self.accept("e-up", self.placeKey, [False])

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

        # Generate world
        cols, rows, layers = 27, 27, 2
        self.blocks = [[[None for _ in range(cols)] for _ in range(layers)] for _ in range(rows)]
        for y in range(layers-1):
            for z in range(rows):
                for x in range(cols):
                    self.add_block(Block(self, 1, random.choice(["stone","dirt","sand","red_wool","iron_block","bricks","netherrack","packed_ice","sponge","soul_soil"]), x-13, y+random.choice([0,1]), z-13))


    def upKey(self, state):
        self.__upKey = state == True
    def leftKey(self, state):
        self.__leftKey = state == True
    def downKey(self, state):
        self.__downKey = state == True
    def rightKey(self, state):
        self.__rightKey = state == True
    def breakKey(self, state):
        self.__breakKey = state == True
    def placeKey(self, state):
        self.__placeKey = state == True

    def camControl(self, task):
        delta = globalClock.getDt()

        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()

            if not self.mouse_reset:
                if not x == 0:
                    self.body.setH(self.body.getH() - x * self.mouse_sensitivity_x)

                if self.cam.getP() < 90 and self.cam.getP() > -90:
                    self.cam.setP(self.cam.getP() + y * self.mouse_sensitivity_y)
                # If the camera is at a -90 or 90 degree angle, this code helps it not get stuck.
                else:
                    if self.cam.getP() > 90:
                        self.cam.setP(self.cam.getP() - 1)
                    elif self.cam.getP() < -90:
                        self.cam.setP(self.cam.getP() + 1)

            self.mouse_reset = False

            self.win.movePointer(0, int(self.win.getProperties().getXSize() / 2),
                                 int(self.win.getProperties().getYSize() / 2))

        if self.__upKey:
            self.body.setY(self.body, self.walk_speed * delta)
        if self.__downKey:
            self.body.setY(self.body, -self.walk_speed * delta)

        if self.__leftKey:
            self.body.setX(self.body, -self.strafe_speed * delta)
        if self.__rightKey:
            self.body.setX(self.body, self.strafe_speed * delta)

        self.cTrav.traverse(self.render)
        if self.targetHandler.getNumEntries() > 0:
            self.targetHandler.sortEntries()
            self.highlight.setPos(self.targetHandler.getEntry(0).getIntoNodePath().getPos())
            self.highlight.show()
        else:
            self.highlight.hide()

        return task.cont

    def add_block(self, block):
        self.blocks[block.x][block.y][block.z] = block


PyCraft().run()
