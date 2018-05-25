import cad
import math
import geom
import tempfile

icon = None
property_titles = ['leading edge', 'trailing edge', 'root profile', 'tip profile', 'angle graph']
sketch_xml_names = ['LeadingEdge', 'TrailingEdge', 'RootProfile', 'TipProfile', 'AngleGraph']
properties = []

class Wing(cad.Object):
    def __init__(self):
        cad.Object.__init__(self)
        self.SetUsesGLList(True)
        global icon
        
        # properties
        self.sketch_ids = [0,0,0,0,0]
        self.values = {
                       'mirror':False,
                       'centre_straight':True,
                       }
        self.color = cad.Color(128, 128, 128)
        
        if icon == None:
            icon = cad.Bitmap('C:/Dev/IbusOrni/trunk/wings/icons/wing.png')
        self.box = None  # if box is None, then the curves need reloading
        self.ResetCurves()
        
    def ResetCurves(self):
        self.curves = []
        for id in self.sketch_ids:
            self.curves.append(None)
                                            
    def Recalculate(self):
        self.KillGLLists()
        self.box = None
        self.ResetCurves()
        
    def SketchesToCurves(self):
        for i in range(0, len(self.sketch_ids)):
            self.curves[i] = GetCurveFromSketch(self.sketch_ids[i])
        self.root_profile_invtm = GetTmFromCurve(self.curves[2])
        self.tip_profile_invtm = GetTmFromCurve(self.curves[3])
        
    def CalculateBox(self):
        self.box = geom.Box3D()
        for i in range(0, len(self.sketch_ids)):
            if self.curves[i] != None:
                curve_box = self.curves[i].GetBox()
                self.box.Insert(geom.Box3D(curve_box.MinX(), curve_box.MinY(), 0.0, curve_box.MaxX(), curve_box.MaxY(), 0.0))

    def GetIcon(self):
        global icon
        return icon
    
    def GetTypeString(self):
        return "Wing"

    def GetUnitizedSectionPoints(self, tip_fraction):
        # the start point will be geom.Point(0,0) and the last point will be geom.Point(1,0)
        pts = []
            
        perim = self.curves[2].Perim()
        cur_perim = 0.0
        prev_v = None
        
        for v in self.curves[2].GetVertices():
            if prev_v != None:
                span = geom.Span(prev_v.p, v, False)
                cur_perim += span.Length()
            fraction = cur_perim / perim
            root_point = GetUnitizedPoint(self.curves[2], fraction, self.root_profile_invtm, self.values['centre_straight'] and (tip_fraction < 0.01))
            if root_point == None: return
            tip_point = GetUnitizedPoint(self.curves[3], fraction, self.tip_profile_invtm, self.values['centre_straight'] and (tip_fraction < 0.01))
            if tip_point == None: return
            vec = tip_point - root_point
            p = root_point + vec * tip_fraction
            pts.append(p)
            prev_v = v
        return pts

    def GetLeadingEdgePoint(self, fraction):
        perim = self.curves[0].Perim()
        return self.curves[0].PerimToPoint(perim * fraction)
        
    def GetTrailingEdgePoint(self, leading_edge_point):
        backward_curve = geom.Curve()
        backward_curve.Append(leading_edge_point)
        backward_curve.Append(leading_edge_point + geom.Point(0, -1000.0))
        pts = backward_curve.Intersections(self.curves[1])
        if len(pts) == 0:
            return None
        return pts[0]
        
    def GetAngle(self, fraction):
        if self.curves[4] == None:
            return 0.0
        box = self.curves[4].GetBox()
        x = box.MinX() + box.Width() * fraction
        curve = geom.Curve()
        curve.Append(geom.Point(x, box.MinY() - 1.0))
        curve.Append(geom.Point(x, box.MaxY() + 1.0))
        pts = curve.Intersections(self.curves[4])
        if len(pts) == 0: return 0.0
        angle = pts[0].y - box.MinY()
        return angle
        
    def GetOrderedSectionPoints(self, fraction):
        leading_edge_p = self.GetLeadingEdgePoint(fraction)
        if leading_edge_p == None: return
        trailing_edge_p = self.GetTrailingEdgePoint(leading_edge_p)
        if trailing_edge_p == None:
            v = geom.Point(0,0)
            length = 0.0
        else:
            v = trailing_edge_p - leading_edge_p
            length = leading_edge_p.Dist(trailing_edge_p)
        pts = self.GetUnitizedSectionPoints(fraction)
        if pts == None: return
        pts2 = []
        a = self.GetAngle(fraction) * 0.01745329251994
        for pt in pts:
            pt.Rotate(a)
            hpoint = leading_edge_p + v * pt.x
            pts2.append(geom.Point3d(hpoint.x, hpoint.y, pt.y * length))
        return pts2

    def DrawSection(self, span):
        xmax = self.curves[1].LastVertex().p.x
        if xmax < 0.001: return
        fraction0 = span.p.x / xmax
        fraction1 = span.v.p.x / xmax
        pts0 = self.GetOrderedSectionPoints(fraction0)
        if pts0 == None: return
        pts1 = self.GetOrderedSectionPoints(fraction1)
        if pts1 == None: return
        
        prev_p0 = None
        prev_p1 = None
        
        for p0, p1 in zip(pts0, pts1):
            DrawTrianglesBetweenPoints(prev_p0, prev_p1, p0, p1, self.values['mirror'])
            prev_p0 = p0
            prev_p1 = p1
        
    def OnRenderTriangles(self):
        if self.box == None:
            self.SketchesToCurves()
            self.CalculateBox()
        
        if self.curves[0] == None:
            return # can't draw anything without a leading edge
        
        # use the spans of trailing edge to define the sections
        for span in self.curves[1].GetSpans():
            self.DrawSection(span)
                
    def GetProperties(self):
        for i in range(0, 5):
            p = PropertySketch(self, i)
            properties.append(p) # to not let it be deleted
            cad.AddProperty(p)
        AddPyProperty('mirror', 'mirror', self)
        AddPyProperty('centre_straight', 'centre_straight', self)
        
    def GetColor(self):
        return self.color
        
    def SetColor(self, col):
        self.color = col
        
    def GetBox(self):
        if self.box == None:
            self.SketchesToCurves()
            self.CalculateBox()

        return self.box.MinX(), self.box.MinY(), self.box.MinZ(), self.box.MaxX(), self.box.MaxY(), self.box.MaxZ()
        
    def WriteXML(self):
        cad.SetXmlValue('col', str(self.color.ref()))
        for i in range(0, len(self.sketch_ids)):
            cad.SetXmlValue(sketch_xml_names[i], str(self.sketch_ids[i]))
        cad.SetXmlValue('mirror', str(self.values['mirror']))
        cad.SetXmlValue('centre_straight', str(self.values['centre_straight']))

def XMLRead():
    new_object = Wing()
    s = cad.GetXmlValue('col')
    if s != '':
        new_object.color = cad.Color(int(s))
    for i in range(0, len(sketch_xml_names)):
        new_object.sketch_ids[i] = int(cad.GetXmlValue(sketch_xml_names[i]))
    s = cad.GetXmlValue('mirror')
    if s != '': new_object.values['mirror'] = bool(s)
    
    return new_object

def GetCurveFromSketch(sketch_id):
    sketch_file_path = tempfile.gettempdir() + '/sketch.dxf'
    sketch = cad.GetObjectFromId(cad.OBJECT_TYPE_SKETCH, sketch_id)
    if sketch == None:
        return
    else:
        sketch.WriteDxf(sketch_file_path)
        area = geom.AreaFromDxf(sketch_file_path)
        curves = area.GetCurves()
        if len(curves)>0:
            curve = curves[0]
            if curve.NumVertices() > 1:
                if curve.FirstVertex().p.x > curve.LastVertex().p.x:
                    curve.Reverse()
                return curve
    return None

class PropertySketch(cad.Property):
    def __init__(self, wing, index):
        cad.Property.__init__(self, cad.PROPERTY_TYPE_INT, property_titles[index], wing)
        self.index = index
        self.wing = wing
        
    def SetInt(self, value):
        self.wing.sketch_ids[self.index] = value
        self.wing.Recalculate()
        
    def GetInt(self):
        return self.wing.sketch_ids[self.index]
    
    def MakeACopy(self, o):
        return PropertySketch(self.wing, self.index)

def DrawTrianglesBetweenPoints(prev_p0, prev_p1, p0, p1, mirror):
    if prev_p0 == None:
        return
    cad.DrawTriangle(prev_p0.x, prev_p0.y, prev_p0.z, p0.x, p0.y, p0.z, p1.x, p1.y, p1.z)
    cad.DrawTriangle(prev_p0.x, prev_p0.y, prev_p0.z, p1.x, p1.y, p1.z, prev_p1.x, prev_p1.y, prev_p1.z)
    if mirror:
        cad.DrawTriangle(-prev_p0.x, prev_p0.y, prev_p0.z, -p1.x, p1.y, p1.z, -p0.x, p0.y, p0.z)
        cad.DrawTriangle(-prev_p0.x, prev_p0.y, prev_p0.z, -prev_p1.x, prev_p1.y, prev_p1.z, -p1.x, p1.y, p1.z)
        

def GetTmFromCurve(curve):
    if curve == None:
        return
    ps = curve.FirstVertex().p
    pe = curve.LastVertex().p
    vx = pe - ps
    vx.Normalize()
    vy = ~vx
    o = geom.Point3d(curve.FirstVertex().p.x, curve.FirstVertex().p.y, 0.0)
    vvx = geom.Vector3d(vx.x, vx.y, 0.0)
    vvy = geom.Vector3d(vy.x, vy.y, 0.0)
    tm = geom.Matrix(o, vvx, vvy)
    return tm.Inverse()

def GetUnitizedPoint(curve, fraction, invtm, centre_straight):
    if curve == None: return
    if centre_straight:
        return geom.Point(fraction, 0.0)
    xdist = curve.LastVertex().p.Dist(curve.FirstVertex().p)
    if xdist < 0.00001:
        return geom.Point(0,0)
    scale = 1.0/xdist
    p = curve.PerimToPoint(curve.Perim() * fraction)
    p.Transform(invtm)
    return geom.Point(p.x * scale, p.y * scale)
    
class PyProperty(cad.Property):
    def __init__(self, title, value_name, object):
        t = cad.PROPERTY_TYPE_INVALID
        if type(object.values[value_name]) == bool: t = cad.PROPERTY_TYPE_CHECK
        elif type(object.values[value_name]) == int: t = cad.PROPERTY_TYPE_INT
        elif type(object.values[value_name]) == float: t = cad.PROPERTY_TYPE_DOUBLE
        elif type(object.values[value_name]) == str: t = cad.PROPERTY_TYPE_STRING
        cad.Property.__init__(self, t, title, object)
        self.value_name = value_name
        self.title = title
        self.recalc = object.Recalculate
        self.pyobj = object
        
    def SetBool(self, value):
        self.pyobj.values[self.value_name] = value
        self.recalc()
        
    def SetInt(self, value):
        self.pyobj.values[self.value_name] = value
        self.recalc()
        
    def SetFloat(self, value):
        self.pyobj.values[self.value_name] = value
        self.recalc()
        
    def SetStr(self, value):
        self.pyobj.values[self.value_name] = value
        self.recalc()
        
    def GetBool(self):
        return self.pyobj.values[self.value_name]
    
    def GetInt(self):
        return self.pyobj.values[self.value_name]
    
    def GetFloat(self):
        return self.pyobj.values[self.value_name]
    
    def GetStr(self):
        return self.pyobj.values[self.value_name]
    
    def MakeACopy(self, o):
        return PyProperty(self.title, self.value_name, self.pyobj)

def AddPyProperty(title, value_name, object):
    p = PyProperty(title, value_name, object)
    properties.append(p) # to not let it be deleted
    cad.AddProperty(p)
 