"""Measure the manufactured datums in both saved boards, independently of the placer."""
import argparse
from pathlib import Path
import pcbnew as k

def xy(p):
    return k.ToMM(p.x),k.ToMM(p.y)
def bounds(item):
    bb=item.GetBoundingBox(False,False) if isinstance(item,k.FOOTPRINT) else item.GetBoundingBox()
    return (*xy(bb.GetOrigin()),*xy(bb.GetEnd()))
def close(label,measured,expected,tol=.002):
    if abs(measured-expected)>tol:raise ValueError(f'{label}: {measured} differs from {expected}')
def actual_bounds(points):
    return min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)
def verify(path):
    if not hasattr(k.SwigPyIterator,'next'):k.SwigPyIterator.next=k.SwigPyIterator.__next__
    board=k.LoadBoard(str(path)); draw=list(board.GetDrawings())
    fps={f.GetReference():f for f in board.GetFootprints()}
    lines=[i for i in draw if isinstance(i,k.PCB_SHAPE) and i.GetShape()==k.SHAPE_T_SEGMENT]
    cut=[p for line in lines if line.GetLayer()==k.Edge_Cuts for p in (xy(line.GetStart()),xy(line.GetEnd()))]
    left,top,right,bottom=actual_bounds(cut)
    glass=[p for line in lines if line.GetLayer()==k.F_Fab and abs(line.GetStartX()-line.GetEndX())>k.FromMM(65)
           for p in (xy(line.GetStart()),xy(line.GetEnd()))]
    gx,gy,gX,gY=actual_bounds(glass)
    edges=[gx-left,right-gX,gy-top]
    for e in edges:close('screen margins',e,edges[0])
    points=[]
    for num in range(1,21):
        f=fps[f'SW{num}']
        for obj in f.GraphicalItems():
            if isinstance(obj,k.PCB_SHAPE) and obj.GetLayer()==k.F_Fab and obj.GetShape()==k.SHAPE_T_RECT:
                points.extend([xy(obj.GetStart()),xy(obj.GetEnd())])
        for pad in f.Pads():
            a,b,A,B=bounds(pad);points.extend(((a,b),(A,B)))
    kx,ky,kX,kY=actual_bounds(points)
    paddings=[kx-left,right-kX,ky-gY,bottom-kY]
    for gap in paddings:close('keypad margin',gap,10)
    legends={d.GetText():xy(d.GetPosition()) for d in draw if isinstance(d,k.PCB_TEXT) and d.GetText().isdecimal()}
    assert len(legends)==20
    windows=[]
    key_refs=set()
    for num in range(1,21):
        sw,led,cap=f'SW{num}',f'LED{num+12}',f'C{num+20}'
        key_refs.update([sw,led,cap])
        x,y=xy(fps[sw].GetPosition());lx,ly=xy(fps[led].GetPosition());tx,ty=legends[f'{num:02d}']
        close('LED X',lx,x);close('LED offset',ly-y,-4.17)
        close('Legend X',tx,x);close('Legend offset',ty-y,4.53)
        if num>5:close('row pitch',y-xy(fps[f'SW{num-5}'].GetPosition())[1],17)
        if num%5!=1:windows.append(x-xy(fps[f'SW{num-1}'].GetPosition())[0])
        for item in [fps[led],fps[cap]]:
            a,b,A,B=bounds(item)
            assert kx<=a and ky<=b and A<=kX and B<=kY,item.GetReference()
    for pitch in windows:close('column pitch',pitch,windows[0])
    hidden=[f for ref,f in fps.items() if ref not in key_refs and f.GetLayer()==k.F_Cu]
    for f in hidden:
        a,b,A,B=bounds(f)
        assert min(a-gx,b-gy,gX-A,gY-B)>=.54999,f.GetReference()
    assert all(fps[n].IsFlipped() for n in ['ANT401','D22']+[f'TP{i}' for i in [1,2,3,4,5,401,402,403,404,405,406]])
    slot_top=min(y for x,y in cut if left+12<x<right-12 and top<y<top+20)
    assert slot_top-top>=4.999
    print(f'{right-left:.3f} × {bottom-top:.3f} mm PCB; glass {gX-gx:.3f} × {gY-gy:.3f} mm.')
    print('Screen left/right/top: '+', '.join(f'{e:.3f}' for e in edges)+' mm.')
    print('Keypad left/right/top/bottom: '+', '.join(f'{e:.3f}' for e in paddings)+' mm.')
    print(f'Center pitch X/Y: {windows[0]:.3f}/17.000 mm; 20 correctly paired switches, pixels, bypasses and legends.')
    print(f'{len(hidden)} other front footprints entirely within glass projection (at least 0.55 mm inset).')
    print(f'Top edge to camera slot: {slot_top-top:.3f} mm. Antenna, USB ESD and 11 service pads on rear.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('study',type=Path);study=p.parse_args().study
    for size in ['34','40']:
        print('Panel '+size);verify(next((study/size).glob('*.kicad_pcb')))
