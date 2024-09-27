from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import TransparencyAttrib


class Hud():
    def __init__(self, base):
        self.__base = base
        self.__frame = DirectFrame(frameColor=(0, 0, 0, 0),
                                   pos=(0, 0, -0.88),
                                   image="textures/gui/sprites/hud/hotbar.png",
                                   scale=(1, 1, 0.12))
        self.__frame.setTransparency(TransparencyAttrib.MAlpha)

        self.__active = DirectLabel(frameColor=(0, 0, 0, 0),
                                    pos=(-0.878, 0, 0.05),
                                    image="textures/gui/sprites/hud/hotbar_selection.png",
                                    scale=(0.132, 1, 1))
        self.__active.reparentTo(self.__frame)

    def select(self, slot):
        self.__active.setX(0.2195 * (slot - 5))
