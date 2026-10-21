from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.gp import gp_Pnt
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.XCAFDoc import XCAFDoc_DocumentTool,XCAFDoc_ColorGen
from OCP.Quantity import Quantity_Color,Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs,STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
import sys
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent

def box(x,y,z,cx=0,cy=0,z0=0):return BRepPrimAPI_MakeBox(gp_Pnt(cx-x/2,cy-y/2,z0),x,y,z).Shape()
def save(parts,name,dims):
 doc=TDocStd_Document(TCollection_ExtendedString(name));sh=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());col=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
 for solid,label,color in parts:
  assert BRepCheck_Analyzer(solid).IsValid()
  l=sh.AddShape(solid,False);TDataStd_Name.Set_s(l,TCollection_ExtendedString(label));col.SetColor(l,Quantity_Color(*color,Quantity_TOC_RGB),XCAFDoc_ColorGen)
 w=STEPCAFControl_Writer();w.SetColorMode(True);w.SetNameMode(True);assert w.Transfer(doc,STEPControl_AsIs);assert w.Write(str(out/name))==IFSelect_RetDone
 rd=STEPControl_Reader();assert rd.ReadFile(str(out/name))==IFSelect_RetDone;rd.TransferRoots();s=rd.OneShape();assert BRepCheck_Analyzer(s).IsValid()
 b=Bnd_Box();BRepBndLib.Add_s(s,b);x0,y0,z0,x1,y1,z1=b.Get();actual=(x1-x0,y1-y0,z1-z0)
 assert all(abs(a-b)<1e-5 for a,b in zip(actual,dims)),actual
 print(name,'valid STEP; dimensions',actual)
# Lite-On Rev B p1 nominal envelope and four pad geometry.
parts=[];body=box(1.6,1.6,.18)
for i,(x,y) in enumerate([(-.425,.6),(.425,.6),(.425,-.6),(-.425,-.6)],1):
 p=box(.55,.4,.18,x,y);body=BRepAlgoAPI_Cut(body,p).Shape();parts.append((p,f'terminal_{i}',(.78,.69,.41)))
parts += [(body,'substrate',(.84,.82,.72)),(box(1.6,1.15,.17,z0=.18),'white_diffused_lens',(.94,.94,.86))]
save(parts,'Generated_LTST-C19HE1WT.step',(1.6,1.6,.35))
# Nexperia SOT883 nominal envelope; terminal thickness illustrative.
parts=[];body=box(1,.6,.48)
for i,(x,y,w,h) in enumerate([(-.325,.175,.26,.16),(-.325,-.175,.26,.16),(.325,0,.26,.51)],1):
 p=box(w,h,.02,x,y);body=BRepAlgoAPI_Cut(body,p).Shape();parts.append((p,f'terminal_{i}',(.72,.74,.76)))
parts.append((body,'moulded_body',(.12,.12,.13)))
save(parts,'Generated_BAT54CM_SOT883.step',(1,.6,.48))
