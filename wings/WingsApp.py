import wx
import os
import sys
import cad
from wing import XMLRead

wings_dir = os.path.dirname(os.path.realpath(__file__))
pycad_dir = os.path.realpath(wings_dir + '/../../../PyCAD/trunk')
sys.path.append(pycad_dir)

from App import App # from CAD
from WingsFrame import WingsFrame

class WingsApp(App):
    def __init__(self):
        App.__init__(self)
        
    def OnInit(self):
        result = super().OnInit()
        cad.RegisterXMLRead("Wing", XMLRead)
        return result
    
    def NewFrame(self):
        return WingsFrame(None)
    
