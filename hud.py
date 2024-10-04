import json
import types
from os.path import exists

from direct.gui.DirectGuiBase import DirectGuiBase, DirectGuiWidget
from direct.gui.DirectLabel import DirectLabel
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TransparencyAttrib, PNMImageHeader, LVector3f, SamplerState, CullBinManager, Texture, NodePath, \
    FrameBufferProperties, WindowProperties, GraphicsPipe, Camera, GraphicsOutput, OrthographicLens, LColor, \
    DirectionalLight, RenderState, CullFaceAttrib, ColorWriteAttrib, LVector2i

from font import Font


class ItemSlot():
    item: str
    count: int
    image_label: DirectLabel
    count_label: DirectLabel
    def __init__(self, image_label: DirectLabel, count_label: DirectLabel, item: str = "", count: int = 0):
        self.image_label = image_label
        self.count_label = count_label
        self.set(item, count)

    def set(self, item, count):
        if item is None or count == 0:
            self.item = ""
            self.count = 0
            self.image_label.hide()
            self.count_label.hide()
        else:
            self.image_label.show()
            if self.item != item:
                self.item = item
                if exists(f"assets/textures/item/{item}.png"):
                    self.image_label.setImage(f"assets/textures/item/{item}.png")
                    self.image_label.component("image0").getTexture().setFormat(Texture.F_srgb_alpha)
                    self.image_label.component("image0").getTexture().setMagfilter(SamplerState.FT_nearest)
                    self.image_label.component("image0").getTexture().setMinfilter(SamplerState.FT_nearest)
                elif exists(f"assets/textures/block/{item}.png"):
                    from block import Block

                    if not self.image_label.hascomponent("image0"):
                        self.image_label.setImage(f"assets/textures/block/empty.png")
                    Block.set_icon_on(self.image_label.component("image0"), item)

            if count > 1:
                self.count_label.show()
            if self.count != count:
                self.count = count
                self.count_label.setText(str(count))


class Hud():
    PIXEL_SCALE = 500
    instance = None

    def __init__(self, base: ShowBase):
        Hud.instance = self
        self._base = base

        # Set up offscreen buffer to render block items
        fb_prop = FrameBufferProperties()
        fb_prop.setRgbColor(True)
        fb_prop.setRgbaBits(8, 8, 8, 8)
        fb_prop.setDepthBits(0)
        win_prop = WindowProperties(size=(32, 32))
        flags = GraphicsPipe.BF_refuse_window
        self.block_buffer: GraphicsOutput = base.graphicsEngine.makeOutput(base.pipe, "Block Item Buffer", -100, fb_prop, win_prop, flags, base.win.getGsg(), base.win)

        from block import Block

        block_camnode = base.makeCamera(self.block_buffer, mask=Block.SHADOW_MASK)
        self.block_scene = NodePath("Block Item Scene")
        block_camnode.reparentTo(self.block_scene)
        self.block_camera: Camera = block_camnode.node()
        lens = OrthographicLens()
        lens.setFilmSize(1.75, 1.75)
        lens.setNearFar(-100, 100)
        self.block_camera.setLens(lens)
        self.block_buffer.setClearColor(LColor(0, 0, 0, 0))
        block_camnode.setPos(-10, -10, 9.9)
        block_camnode.setHpr(-45, -35, 0)
        itemsun = DirectionalLight("item_sun")
        itemsun.getLens().setFilmSize(100, 100)
        itemsun.getLens().setNearFar(0.1, 20)
        itemsun.setColorTemperature(7000)
        itemsun.color = itemsun.color * 4
        itemsun.setInitialState(RenderState.make(CullFaceAttrib.makeReverse(), ColorWriteAttrib.make(ColorWriteAttrib.COff)))
        itemsun.setCameraMask(Block.SHADOW_MASK)
        itemsun = self.block_scene.attachNewNode(itemsun)
        itemsun.setPosHpr(0,0,10,-60,-55,0)
        self.block_scene.setLight(itemsun)


        (self.__hotbar, self.__hotbar_image)\
            = self.make_label(name="Hotbar",
                              image_file="assets/textures/gui/sprites/hud/hotbar.png",
                              pos=(base.win.getXSize()/2, -base.win.getYSize()), anchor=(0, 0), align=(0, -1), parent=base.pixel2d)
        self.__hotbar.setTransparency(TransparencyAttrib.MAlpha)
        self.__hotbar.setBin("fixed", 0)

        (self.__active_slot, self.__active_slot_image)\
            = self.make_label(name="ActiveSlot",
                              image_file="assets/textures/gui/sprites/hud/hotbar_selection.png",
                              parent=self.__hotbar)
        self.__active_slot.setBin("fixed", 1)

        self.__hotbarx = self.__hotbar_image.pixel_size.x
        diff = (self.__active_slot_image.pixel_size.x - (self.__hotbarx / 9)) / 2
        self.__hotbar_over_x = self.__hotbar_image.pixel_size.x / (self.__hotbar_image.pixel_size.x + diff)

        self.__font = Font(base, "assets/font/include/default.json")

        self.__slot = [None, None, None, None, None, None, None, None, None]
        for i in range(9):
            (slot, _)\
                = self.make_label(name=f"Slot{i}",
                                  image_file="assets/textures/block/empty.png",
                                  parent=self.__hotbar)
            slot.setX(self.__hotbarx * (i - 4) * self.__hotbar_over_x * 2 / 9)
            slot.setBin("fixed", 2)
            (label, _)\
                = self.make_label(name=f"Slot{i}Count", text=f"0", pos=(0, 0), anchor=(1, 1), align=(-12, 0),
                                  parent=slot,
                                  text_fg=Block.color_from_hex("#FFFFFF"),
                                  text_shadow=(0, 0, 0, 1),
                                  text_scale=(26.0, 26.0),
                                  text_font=self.__font.font
                                  )
            slot.hide()
            self.__slot[i] = ItemSlot(slot, label)

        (self.__level, _)\
            = self.make_label(name=f"Level",
                              text="0", pos=(0, 0), anchor=(0, -1), align=(0, -12),
                              parent=self.__hotbar,
                              text_fg=Block.color_from_hex("#7FFC1F"),
                              text_shadow=(0, 0, 0, 1),
                              text_scale=(32.0, 32.0),
                              text_font=self.__font.font
                              )

        self.select_slot(1)

    def get_image(self, path):
        result = types.SimpleNamespace()
        if "/block/" in path:
            result.path = "assets/textures/block/empty.png"
            result.pixel_size = LVector2i(32, 32)
        else:
            pnm = PNMImageHeader()
            pnm.readHeader(path)
            result.path = path
            result.pixel_size = pnm.getSize()

        (x, y) = result.pixel_size
        result.aspect_scale = LVector3f(1, 1, y / x) if x > y else LVector3f(x / y, 1, 1)
        result.scale = LVector3f(x, 1, y)
        return result

    def make_label(self, name=None, image_file=None, text=None, parent:DirectGuiWidget=None, pos=(0, 0), anchor=(0, 0), align=(0, 0), **kw):
        (px, py) = pos
        (ax, ay) = anchor
        (lx, ly) = align
        px += ax * (1 if parent is None or not isinstance(parent, DirectGuiWidget) else parent.getWidth()/2)
        py -= ay * (1 if parent is None or not isinstance(parent, DirectGuiWidget) else parent.getHeight()/2)
        if image_file is None:
            px += lx
            py -= ly
            label = DirectLabel(frameColor=(0, 0, 0, 0),
                                text=text,
                                pos=(px, 0, py),
                                parent=parent,
                                **kw)
            label.node().setName(name)
            return (label, None)
        else:
            image = self.get_image(image_file)
            px += lx * image.pixel_size.x
            py -= ly * image.pixel_size.y
            label = DirectLabel(frameColor=(0, 0, 0, 0),
                                pos=(px, 0, py),
                                image=image.path,
                                image_scale=image.scale,
                                parent=parent)
            label.node().setName(name)
            label.component("image0").getTexture().setFormat(Texture.F_srgb_alpha)
            label.component("image0").getTexture().setMagfilter(SamplerState.FT_nearest)
            label.component("image0").getTexture().setMinfilter(SamplerState.FT_nearest)
            return (label, image)


    @staticmethod
    def multiply(s1: LVector3f, s2: LVector3f) -> LVector3f:
        return LVector3f(s1.x*s2.x, s1.y*s2.y, s1.z*s2.z)

    def select_slot(self, slot):
        self.__active_slot.setX(self.__hotbarx * (slot - 5) * self.__hotbar_over_x * 2 / 9)

    def set_slot(self, slot, item, count):
        self.__slot[slot - 1].set(item, count)

