import types

from direct.gui.DirectGuiBase import DirectGuiBase
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import TransparencyAttrib, PNMImageHeader, LVector3f

from block import Block


class Hud():
    PIXEL_SCALE = 500

    def __init__(self, base):
        self.__base = base

        self.__hotbar = self.make_label(image_file="textures/gui/sprites/hud/hotbar.png",
                                        anchor=(0, -1), align=(0, -1))
        self.__hotbar.setTransparency(TransparencyAttrib.MAlpha)
        self.__hotbar.resetFrameSize()

        self.__active_slot = self.make_label(image_file="textures/gui/sprites/hud/hotbar_selection.png",
                                             parent=self.__hotbar)

        self.select_slot(1)

        self.__level = DirectLabel(frameColor=(0, 0, 0, 0),
                                   text_fg=Block.color_from_hex("#7FFC1F"),
                                   text="0",
                                   pos=(0, 0, self.__hotbar["image_scale"].z + 12 / Hud.PIXEL_SCALE),
                                   text_shadow=(0, 0, 0, 1),
                                   text_scale=(.1,.1),
                                   parent=self.__hotbar)

    @staticmethod
    def get_image(path):
        pnm = PNMImageHeader()
        pnm.readHeader(path)
        result = types.SimpleNamespace()
        result.path = path
        result.pixel_size = pnm.getSize()
        (x, y) = result.pixel_size
        result.aspect_scale = LVector3f(1, 1, y / x) if x > y else LVector3f(x / y, 1, 1)
        result.scale = max(x, y) / Hud.PIXEL_SCALE
        result.scale = LVector3f(result.scale, 1, result.scale)
        return result

    def make_label(self, image_file=None, parent:DirectGuiBase=None, pos=(0, 0), anchor=(0, 0), align=(0, 0)):
        image = Hud.get_image(image_file)
        (px, py) = pos
        (ax, ay) = anchor
        (lx, ly) = align
        px += ax - lx * image.pixel_size.x / Hud.PIXEL_SCALE
        py += ay - ly * image.pixel_size.y / Hud.PIXEL_SCALE
        return DirectLabel(frameColor=(0, 0, 0, 0),
                           pos=(px, 0, py),
                           image=image.path,
                           image_scale=image.aspect_scale,
                           scale=image.scale if parent is None else image.scale / parent["scale"].x,
                           parent=parent)

    @staticmethod
    def multiply(s1: LVector3f, s2: LVector3f) -> LVector3f:
        return LVector3f(s1.x*s2.x, s1.y*s2.y, s1.z*s2.z)

    def select_slot(self, slot):
        self.__active_slot.setX((slot - 5) * 364 / 368 * 2 / 9)
