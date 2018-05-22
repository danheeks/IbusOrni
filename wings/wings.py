import cad
import wings.wing

cad.AddMenu('Wings')

def OnWing():
    o = wings.wing.Wing()
    cad.PyIncRef(o)
    cad.AddObject(o)
        
cad.AddMenuItem('Add a Wing', OnWing)

cad.RegisterXMLRead("Wing", wings.wing.XMLRead)
    
#cad.RegisterReadXMLfunction('Wing', OnReadWing)
