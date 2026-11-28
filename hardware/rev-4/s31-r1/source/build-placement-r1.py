"""Build KiCad placement studies. Retain R3A hardpoints; load new pads from libraries and assign actual schematic nets."""
import argparse
import json
import math
from pathlib import Path
import re
import tempfile
from xml.etree import ElementTree as ET
import pcbnew as k

def vec(x,y): return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def point(p): return (k.ToMM(p.x),k.ToMM(p.y))
def line(board,layer,a,b,width=.16):
    s=k.PCB_SHAPE(board);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(vec(*a));s.SetEnd(vec(*b));s.SetLayer(layer);s.SetWidth(k.FromMM(width));board.Add(s)
def arc(board,layer,a,m,b):
    s=k.PCB_SHAPE(board);s.SetShape(k.SHAPE_T_ARC);s.SetArcGeometry(vec(*a),vec(*m),vec(*b));s.SetLayer(layer);s.SetWidth(k.FromMM(.05));board.Add(s)
def rectangle(board,layer,x,y,w,h):
    pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
    for i in range(4):line(board,layer,pts[i],pts[(i+1)%4])
def mark(board,layer,x,y,caption):
    o=k.PCB_TEXT(board);o.SetLayer(layer);o.SetText(caption);o.SetPosition(vec(x,y));o.SetTextSize(vec(.85,.85));o.SetTextThickness(k.FromMM(.13));board.Add(o)
def rounded_edge(board,x,y,w,h):
    r=2; d=r-r/math.sqrt(2); x2=x+w;y2=y+h
    for a,b in [((x+r,y),(x2-r,y)),((x2,y+r),(x2,y2-r)),((x2-r,y2),(x+r,y2)),((x,y2-r),(x,y+r))]: line(board,k.Edge_Cuts,a,b,.05)
    for a,m,b in [((x,y+r),(x+d,y+d),(x+r,y)),((x2-r,y),(x2-d,y+d),(x2,y+r)),((x2,y2-r),(x2-d,y2-d),(x2-r,y2)),((x+r,y2),(x+d,y2-d),(x,y2-r))]:arc(board,k.Edge_Cuts,a,m,b)
def area(board,name,layer,bb,rf=False):
    z=k.ZONE(board);z.SetIsRuleArea(True);z.SetZoneName(name)
    if rf:z.SetLayerSet(k.LSET.AllCuMask(board.GetCopperLayerCount()))
    else:z.SetLayer(layer)
    z.SetDoNotAllowFootprints(not rf);z.SetDoNotAllowPads(False);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(rf);z.SetDoNotAllowZoneFills(rf)
    x,y,X,Y=bb;outline=z.Outline();outline.NewOutline()
    for pos in [(x,y),(X,y),(X,Y),(x,Y)]:outline.Append(*tuple(vec(*pos)))
    board.Add(z)
def box(f):
    b=f.GetBoundingBox(False,False)
    return (*point(b.GetOrigin()),*point(b.GetEnd()))
def hits(a,b,g=.25):
    return a[0]<b[2]+g and b[0]<a[2]+g and a[1]<b[3]+g and b[1]<a[3]+g
def component_fp(libroot,libid):
    name,part=libid.split(':'); path=libroot/(name+'-r1.pretty') if name in ['LAB','LABR4'] else Path('/usr/share/kicad/footprints')/(name+'.pretty')
    f=k.FootprintLoad(str(path),part)
    if not f:raise ValueError(f'Footprint {libid} at {path}')
    f.SetFPID(k.LIB_ID(name,part));return f
def put(f,x,y,back=False,angle=0):
    if back!=(f.GetLayer()==k.B_Cu):f.Flip(f.GetPosition(),k.FLIP_DIRECTION_TOP_BOTTOM)
    f.SetOrientationDegrees(angle);f.SetPosition(vec(x,y))
def build(args):
    dest=args.project.parent; variant=dest.name; doc=json.loads((Path(__file__).parent/'panel-envelopes-r1.json').read_text())[variant]
    base=args.baseline; old=k.LoadBoard(str(base)); raw=base.read_text(); blocks=re.split(r'(?=^\t\([\w]+[\s)])',raw[:raw.rfind('\n)')],flags=re.M)
    # Import stack-up and silk key legends only. Start with an empty copper database.
    types={'version','generator','generator_version','general','paper','layers','setup'}
    keep=[blocks[0]]+[b for b in blocks[1:] if re.match(r'\t\((\w+)',b)[1] in types or re.match(r'\t\(gr_text "(\d{2}|INT|EXT)"',b)]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/'stack.kicad_pcb';tmp.write_text(''.join(keep)+'\n)\n');board=k.LoadBoard(str(tmp))
    refs={f.GetReference():f for f in old.GetFootprints()};r=ET.parse(args.netlist); nets={}; pins={}; placed={k.F_Cu:[],k.B_Cu:[]}
    for net in r.findall('nets/net'):
        obj=k.NETINFO_ITEM(board,net.get('name').replace('/','{slash}'));board.Add(obj);nets[net.get('name')]=obj
        for nd in net.findall('node'):pins[nd.get('ref'),nd.get('pin')]=(obj,nd)
    w=doc['board_width'];h=doc['board_height'];left=101-w/2;top=192-h;px=101-doc['width']/2;py=top+8;ax=px+doc['active_left'];ay=py+doc['active_top']
    cx=ax+doc['active']/2;cy=ay+doc['active']/2
    rounded_edge(board,left,top,w,h)
    rectangle(board,k.F_Fab,px,py,doc['width'],doc['height']);rectangle(board,k.Dwgs_User,ax,ay,doc['active'],doc['active'])
    mark(board,k.Dwgs_User,101,py+2.4,doc['product']+'  '+str(doc['pixels'])+' sq')
    area(board,'Jauch 246524 bonded pouch · reverse-side no-placement',k.B_Cu,(71.25,92,130.75,170.5))
    for x in (73,117):area(board,'microSD removal path',k.B_Cu,(x,194,x+12,202))
    # The rear lens is centered on the active image. Its flex passes through a racetrack slot behind the display.
    lens=(cx-4.25,cy-4.25,cx+4.25,cy+4.25)
    rectangle(board,k.B_Fab,lens[0],lens[1],8.5,8.5)
    line(board,k.Cmts_User,(cx-2,cy),(cx+2,cy));line(board,k.Cmts_User,(cx,cy-2),(cx,cy+2))
    rectangle(board,k.B_Fab,71.25,92,59.5,78.5)
    mark(board,k.Cmts_User,101,133,'Jauch 246524 · 59.5 x 78.5 max')
    antenna_corner=(left,top,left+7.05,top+7.05);area(board,'Johanson antenna · all-layer ground clearance',k.F_Cu,antenna_corner,True)
    # RF feed components intentionally occupy the feed-side edge.
    placed[k.F_Cu].append((antenna_corner,'antenna clearance'));placed[k.B_Cu]+=[(antenna_corner,'antenna clearance'),((71.25,92,130.75,170.5),'battery')]
    sy=cy-32
    line(board,k.Edge_Cuts,(cx-5,sy-2),(cx+5,sy-2),.05)
    line(board,k.Edge_Cuts,(cx-5,sy+2),(cx+5,sy+2),.05)
    arc(board,k.Edge_Cuts,(cx-5,sy-2),(cx-7,sy),(cx-5,sy+2))
    arc(board,k.Edge_Cuts,(cx+5,sy+2),(cx+7,sy),(cx+5,sy-2))
    camera_corridor=(cx-7.0,cy-34.35,cx+7.0,cy+4.5)
    placed[k.B_Cu].append((camera_corridor,'camera and fold'))
    rectangle(board,k.B_Fab,camera_corridor[0],camera_corridor[1],14,38.85)
    area(board,'Seeed optical head and flex to slot',k.B_Cu,camera_corridor)
    front_flex=(cx-7.0,cy-34.35,cx+7.0,cy-1.36)
    placed[k.F_Cu].append((front_flex,'camera flex to socket'))
    rectangle(board,k.F_Fab,front_flex[0],front_flex[1],14,32.99)
    area(board,'Camera flex under display, slot to J501 mouth',k.F_Cu,(cx-7,cy-34.35,cx+7,cy-2.0))
    # Screen tail folds underneath; the pad origin follows each drawing's asymmetric tongue.
    jx=px+doc['tongue_center_x'];jy=py+doc['height']-(doc['tail_extension']-math.pi*1.5-2.0)-1.125
    fixed={'J601':(jx,jy,False,0),'J501':(cx,cy-1.262389+5.70,False,180),'ANT401':(left+2.25,top+3.05,False,90)}
    reserve_lcd=(jx-11,jy+3.3,jx+11,py+doc['height']+2.5)
    placed[k.F_Cu].append((reserve_lcd,'panel tail'))
    rectangle(board,k.F_Fab,reserve_lcd[0],reserve_lcd[1],22,reserve_lcd[3]-reserve_lcd[1])
    pending=[];fitted={}
    footprint_order=lambda c: (0 if c.get('ref') in fixed else 1 if c.get('ref').startswith(('MK','LED','SW','LS','J')) else 2, c.get('ref'))
    for c in sorted(r.findall('components/comp'),key=footprint_order):
        ref=c.get('ref'); libid=c.findtext('footprint') or ''
        if not libid:continue
        retain=ref in refs and refs[ref].GetFPIDAsString()==libid and ref not in {'U1','U9','Y1'}
        f=k.FOOTPRINT(refs[ref]) if retain else component_fp(dest.parent/'libraries',libid)
        f.SetReference(ref);f.SetValue(c.findtext('value') or '');f.SetDNP(c.find('property[@name="dnp"]') is not None)
        sp=c.find('sheetpath');f.SetPath(k.KIID_PATH(sp.get('tstamps')+c.findtext('tstamps')));f.SetSheetfile(c.find('property[@name="Sheetfile"]').get('value'));f.SetSheetname(sp.get('names').strip('/'))
        # Imported footprints contain nets from Rev 3A. Replace all pad pointers on all footprints.
        for pad in f.Pads():
            entry=pins.get((ref,pad.GetNumber()))
            if entry:
                obj,node=entry;pad.SetNet(obj);pad.SetPinFunction(node.get('pinfunction') or '');pad.SetPinType(node.get('pintype') or '')
            else:pad.SetNetCode(0)
        for field in c.findall('fields/field'):
            key=field.get('name')
            if key not in ('Footprint','Value','Reference'):
                f.SetField(key,field.text or '')
                f.GetField(key).SetVisible(False)
        if c.find('property[@name="exclude_from_bom"]') is not None:
            f.SetAttributes(f.GetAttributes()|k.FP_EXCLUDE_FROM_BOM)
        else:f.SetAttributes(f.GetAttributes() & ~k.FP_EXCLUDE_FROM_BOM)
        if not retain: f.Reference().SetVisible(False);f.Value().SetVisible(False)
        board.Add(f);fitted[ref]=f
        if ref in fixed:
            put(f,*fixed[ref]);placed[f.GetLayer()].append((box(f),ref));continue
        if not retain:pending.append((ref,f,None));continue
        x,y=point(f.GetPosition()); back=f.GetLayer()==k.B_Cu
        if ref=='J5':f.SetPosition(vec(left+1.5,y))
        if ref=='SW21':f.SetPosition(vec(left+w-6,y))
        if re.fullmatch(r'LED(?:[1-9]|1[012])',ref): f.SetPosition(vec(left+3.5 if x<101 else left+w-3.5,y))
        if ref in ('MK1','MK3','MK2','MK4'): f.SetPosition(vec(x+(left-64 if x<101 else 64-left),y))
        hard=ref.startswith(('MK','LED','SW','LS','J'))
        if hard:
            for pad in f.Pads():
                if pad.GetDrillSize().x>0:
                    pos=pad.GetPosition();size=pad.GetDrillSize();x0,y0=point(pos);a,b=point(size)
                    placed[k.F_Cu if back else k.B_Cu].append(((x0-a/2-.2,y0-b/2-.2,x0+a/2+.2,y0+b/2+.2),'through hole'))
        if hard or not any(hits(box(f),bb,0) for bb,_ in placed[f.GetLayer()]):placed[f.GetLayer()].append((box(f),ref))
        else:pending.append((ref,f,(x,y,back)))
    anchors={'U1':(left+19,top+20),'U9':(left+27,top+27),'Y1':(left+14,top+29),'U401':(114,86),'U501':(cx-11,cy+4),'U502':(cx+11,cy+6),'U503':(cx-8,cy-2),'U504':(cx+7,cy-2),'U505':(cx+13,cy+5),'U601':(jx+15,jy-4)}
    hostpower=(left+19,top+20);hostflash=(left+26,top+27);hostrf=(left+8,top+6);hostboot=(left+14,top+30)
    for ref,f,previous in sorted(pending,key=lambda item:-(box(item[1])[2]-box(item[1])[0])*(box(item[1])[3]-box(item[1])[1])):
        sheet=f.GetSheetfile()
        center=anchors.get(ref)
        if not center:
            if previous:center=previous[:2]
            elif 'radio.' in sheet:center=hostrf
            elif 'flash.' in sheet:center=hostflash
            elif 'boot.' in sheet:center=hostboot
            elif 'host' in sheet:center=hostpower
            elif 'camera' in sheet:center=(cx,cy-1.5)
            else:center=(jx+13,jy-3)
        back=previous[2] if previous else False;ang=f.GetOrientationDegrees() if previous else 0;put(f,0,0,back,ang);dx,dy,dX,dY=box(f)
        candidates=[]
        y=max(top+2.5-dy,center[1]-60);ystart=math.ceil(y*2)/2
        for iy in range(int((min(190-dY,center[1]+60)-ystart)*2)+1):
            py2=ystart+iy*.5
            if abs(py2-center[1])>30 and not previous: continue
            xstart=math.ceil((left+1.0-dx)*2)/2
            for ix in range(int((left+w-1-dX-xstart)*2)+1):
                xx=xstart+ix*.5;candidates.append(((xx-center[0])**2+(py2-center[1])**2,xx,py2))
        for _,x,y in sorted(candidates):
            bb=(x+dx,y+dy,x+dX,y+dY)
            if not any(hits(bb,other,.4) for other,_ in placed[f.GetLayer()]):
                f.SetPosition(vec(x,y));placed[f.GetLayer()].append((bb,ref));break
        else:raise ValueError('No placement for '+ref)
    if 'J501' not in fitted or 'U1' not in fitted:raise ValueError('missing primary hardware')
    output=args.project.with_suffix('.kicad_pcb')
    # pcbnew also writes settings next to SaveBoard; retain the electrical project's reviewed rule set.
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td)/output.name;k.SaveBoard(str(temp),board);output.write_bytes(temp.read_bytes())
    output.write_text(output.read_text().replace('${KIPRJMOD}/models-v5/','${KIPRJMOD}/../libraries/models-v5/'))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('project',type=Path);p.add_argument('netlist',type=Path);build(p.parse_args())
