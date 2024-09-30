import types

from direct.gui.DirectGuiBase import DirectGuiBase, DirectGuiWidget
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import TransparencyAttrib, PNMImageHeader, LVector3f, SamplerState, CullBinManager, Texture

from block import Block
from font import Font


class Hud():
    PIXEL_SCALE = 500

    def __init__(self, base):
        self.__base = base

        (self.__hotbar, self.__hotbar_image)\
            = self.make_label(name="Hotbar",
                              image_file="textures/gui/sprites/hud/hotbar.png",
                              pos=(base.win.getXSize()/2, -base.win.getYSize()), anchor=(0, 0), align=(0, -1), parent=base.pixel2d)
        self.__hotbar.setTransparency(TransparencyAttrib.MAlpha)
        self.__hotbar.setBin("fixed", 0)

        (self.__active_slot, self.__active_slot_image)\
            = self.make_label(name="ActiveSlot",
                              image_file="textures/gui/sprites/hud/hotbar_selection.png",
                              parent=self.__hotbar)
        self.__active_slot.setBin("fixed", 1)

        self.__hotbarx = self.__hotbar_image.pixel_size.x
        diff = (self.__active_slot_image.pixel_size.x - (self.__hotbarx / 9)) / 2
        self.__hotbar_over_x = self.__hotbar_image.pixel_size.x / (self.__hotbar_image.pixel_size.x + diff)

        self.__font = Font(base, "font/include/default.json")

        self.__slot = [None, None, None, None, None, None, None, None, None]
        for i in range(9):
            (slot, _)\
                = self.make_label(name=f"Slot{i}",
                                  image_file="textures/item/apple.png",
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
            self.__slot[i] = {"label": slot, "count_label": label}

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

    @staticmethod
    def get_image(path):
        pnm = PNMImageHeader()
        pnm.readHeader(path)
        result = types.SimpleNamespace()
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
            image = Hud.get_image(image_file)
            px += lx * image.pixel_size.x
            py -= ly * image.pixel_size.y
            label = DirectLabel(frameColor=(0, 0, 0, 0),
                                pos=(px, 0, py),
                                image=image.path,
                                image_scale=image.scale,
                                # scale=image.scale if parent is None or parent is not DirectGuiBase else image.scale / parent["scale"].x,
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

    def set_slot(self, slot, item):
        self.__slot[slot - 1]["label"].setImage(item)
        self.__slot[slot - 1]["label"].component("image0").getTexture().setFormat(Texture.F_srgb_alpha)
        self.__slot[slot - 1]["label"].component("image0").getTexture().setMagfilter(SamplerState.FT_nearest)
        self.__slot[slot - 1]["label"].component("image0").getTexture().setMinfilter(SamplerState.FT_nearest)

