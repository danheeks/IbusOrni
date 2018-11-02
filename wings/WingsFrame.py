import sys
import os
import wx
from wing import Wing
import cad

wings_dir = os.path.dirname(os.path.realpath(__file__))
pycad_dir = os.path.realpath(wings_dir + '/../../PyCAD/trunk')
sys.path.append(pycad_dir)
wings = []

from Frame import Frame # from CAD

class WingsFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        
    def OnWing(self, e):
        o = Wing()
        wings.append(o)
        cad.AddUndoably(o, None, None)

    def AddExtraMenus(self):
        self.bitmap_path = wings_dir + '/icons'
        self.AddMenu('&Wings')
        self.AddMenuItem('Add a Wing', self.OnWing, None, 'wing')        
