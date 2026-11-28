"""Draw the two mechanical fit sheets from their KiCad placement boards, at 1:1.

Run with a ReportLab Python. KiCad's system Python is used only to extract the
board geometry. Supply --study pointing to the directory with 34/, 40/, source/.
"""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OUTPUT = "LAB-Pocket-S31-panel-fit-letter-r1.pdf"


def read_board(filename):
    import pcbnew as k
    if not hasattr(k.SwigPyIterator, "next"):
        k.SwigPyIterator.next = k.SwigPyIterator.__next__
    board = k.LoadBoard(str(filename))

    def xy(pt):
        return [round(k.ToMM(pt.x), 5), round(k.ToMM(pt.y), 5)]

    def outline(shape):
        kind = shape.GetShapeStr()
        start, end = xy(shape.GetStart()), xy(shape.GetEnd())
        if kind in ("Line", "Rect"):
            return [kind, start, end]
        if kind == "Circle":
            return [kind, start, k.ToMM(shape.GetRadius())]
        if kind == "Polygon":
            return [kind, [xy(p) for p in shape.GetPolyPoints()]]
        if kind == "Arc":
            x, y = xy(shape.GetCenter())
            a = math.atan2(start[1]-y, start[0]-x)
            r = math.hypot(start[0]-x, start[1]-y)
            sweep = shape.GetArcAngle().AsRadians()
            points = [(x+r*math.cos(a+i*sweep/24), y+r*math.sin(a+i*sweep/24)) for i in range(25)]
            assert math.dist(points[-1], end) < .002
            return ["Path", points]
        raise ValueError(kind)

    parts = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        shapes = [outline(z) for z in fp.GraphicalItems()
                  if isinstance(z, k.PCB_SHAPE) and z.GetLayer() in (k.F_Fab, k.B_Fab)]
        keypads = []
        if ref.startswith("SW") and ref != "SW21":
            for pad in fp.Pads():
                box = pad.GetBoundingBox()
                keypads.append([xy(box.GetOrigin()), xy(box.GetEnd())])
        parts[ref] = dict(back=fp.IsFlipped(), position=xy(fp.GetPosition()), shapes=shapes, pads=keypads)
    edges = [outline(z) for z in board.GetDrawings() if isinstance(z, k.PCB_SHAPE) and z.GetLayer() == k.Edge_Cuts]
    keylegends = {z.GetText(): xy(z.GetPosition()) for z in board.GetDrawings()
                  if isinstance(z, k.PCB_TEXT) and z.GetText().isdecimal()}
    zones = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            poly = z.Outline().Outline(0)
            zones[z.GetZoneName()] = [xy(poly.CPoint(i)) for i in range(poly.PointCount())]
    return dict(parts=parts, edges=edges, legends=keylegends, zones=zones)


class Sheet:
    """Physical coordinates are in millimetres from the top left of the page."""
    def __init__(self, pdf, panel, board):
        self.c = pdf
        self.p = panel
        self.b = board
        self.w = panel["board_width"]
        self.h = panel["board_height"]
        self.top = 29
        self.fr, self.rr = 80-self.w/2, 203-self.w/2
        self.left, self.pcbtop = 101-self.w/2, 192-self.h
        self.px, self.py = 101-panel['width']/2, self.pcbtop+8
        self.ax, self.ay = self.px+panel['active_left'], self.py+panel['active_top']
        self.cx, self.cy = self.ax+panel['active']/2, self.ay+panel['active']/2
        self.c.setStrokeGray(0)
        self.c.setFillGray(0)

    def coord(self, x, y):
        from reportlab.lib.units import mm
        return x*mm, (215.9-y)*mm

    def map(self, face, xy):
        x, y = xy
        return ((self.fr+x-self.left) if face == 'F' else (self.rr+self.w-x+self.left),
                self.top+y-self.pcbtop)

    def line(self, pts, width=.45, close=False, dash=False, fill=False):
        self.c.saveState()
        self.c.setLineWidth(width)
        self.c.setLineJoin(1)
        self.c.setLineCap(1)
        if dash:
            self.c.setDash(3.1, 2.4)
        path = self.c.beginPath()
        path.moveTo(*self.coord(*pts[0]))
        for xy in pts[1:]:
            path.lineTo(*self.coord(*xy))
        if close:
            path.close()
        if fill:
            self.c.setFillGray(1)
        self.c.drawPath(path, fill=int(fill), stroke=1)
        self.c.restoreState()

    def rect(self, face, x, y, w, h, line=.45, fill=False, dash=False):
        self.line([self.map(face, pt) for pt in ((x,y),(x+w,y),(x+w,y+h),(x,y+h))],
                  line, close=True, dash=dash, fill=fill)

    def ellipse(self, face, x, y, r, weight=.45):
        from reportlab.lib.units import mm
        self.c.setLineWidth(weight)
        self.c.circle(*self.coord(*self.map(face,(x,y))),r*mm,stroke=1,fill=0)

    def label(self, x, y, text, size=7, align='center', bold=False, rotate=False, knockout=False):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        self.c.saveState()
        self.c.translate(*self.coord(x,y))
        if rotate: self.c.rotate(90)
        self.c.setFont(font,size)
        text_width = stringWidth(text,font,size)
        dx = -text_width/2 if align=='center' else -text_width if align=='right' else 0
        if knockout:
            self.c.setFillGray(1)
            self.c.rect(dx-2,-1.8,text_width+4,size+2,stroke=0,fill=1)
            self.c.setFillGray(0)
        self.c.drawString(dx,0,text)
        self.c.restoreState()

    def inside(self, face, x, y, text, size=6.3, **kwargs):
        self.label(*self.map(face,(x,y)),text,size,**kwargs)

    def shape(self, face, shape, weight=.35, dash=False):
        kind, *args = shape
        if kind == 'Circle':
            self.ellipse(face,*args[0],args[1],weight)
        elif kind == 'Rect':
            (x,y),(xx,yy)=args
            self.rect(face,x,y,xx-x,yy-y,weight,dash=dash)
        else:
            points = args if kind == 'Line' else args[0]
            self.line([self.map(face,p) for p in points],weight,close=kind=='Polygon',dash=dash)

    def dim_h(self, x1, x2, y, name):
        for x in (x1, x2):
            self.line([(x,y-1.1),(x,y+1.1)],.37)
        self.line([(x1,y),(x2,y)],.38)
        self.label((x1+x2)/2,y+.84,name,6.9,knockout=True)

    def dim_v(self, y1, y2, x, name):
        for y in (y1,y2):
            self.line([(x-1.15,y),(x+1.15,y)],.37)
        self.line([(x,y1),(x,y2)],.38)
        self.label(x+.78,(y1+y2)/2,name,6.9,rotate=True,knockout=True)

    def fitted(self, face, part, ref):
        major = ref.startswith(('LED','SW','MK','LS','J'))
        weight = .5 if major else .21
        for s in part['shapes']:
            # DM3AT F.Fab contains fully ejected and seated card outlines;
            # the rear drawing shows just the socket, without removable media.
            if ref in ('J3','J4'):
                points = s[1:] if s[0]=='Line' else s[1]
                if max(pt[1] for pt in points) > 190.535:
                    continue
            self.shape(face,s,weight)
        for (x,y),(xx,yy) in part['pads']:
            self.rect(face,x,y,xx-x,yy-y,.23)
        x,y = part['position']
        if ref.startswith('LS'):
            self.inside(face,x,y+.8,'SPK '+ref[2:],7,bold=True)
        if ref.startswith('MK'):
            left_edge = self.map(face,(x,y))[0] < self.rr+self.w/2
            margin = self.rr-2.5 if left_edge else self.rr+self.w+2.5
            self.label(margin,self.map(face,(x,y))[1]+.75,'Mic '+ref[2:],6.0,'right' if left_edge else 'left')
        if ref=='SW21':
            self.label(self.rr-2.5,self.map(face,(x,y))[1]+.8,'Power switch',6.2,'right')
        if ref.startswith('LED') and int(ref[3:]) <= 12:
            self.inside(face,x,y+.62,'L'+ref[3:],4.5,knockout=True)
        labels = {'J1':'USB-C','J3':'SD INT','J4':'SD EXT','J5':'AUDIO IN','J6':'BAT'}
        if ref in labels:
            if ref=='J5': x+=7
            if ref=='J6': y-=1.2
            self.inside(face,x,y+.77,labels[ref],5.8,bold=True,knockout=True)

    def front(self):
        F='F'
        for ref,part in self.b['parts'].items():
            if not part['back'] and ref not in ('J501','J601'):
                self.fitted(F,part,ref)
        for ref,pt in self.b['legends'].items():
            self.inside(F,pt[0],pt[1]+.58,ref,5.65,bold=True)
        w,h,a = self.p['width'],self.p['height'],self.p['active']
        self.rect(F,self.px,self.py,w,h,.68,fill=True)
        self.rect(F,self.ax,self.ay,a,a,.53)
        # Locate both concealed sockets from their true fabricator-outline
        # bounds. Dashed envelopes keep the front panel simultaneously readable.
        for ref in ('J501','J601'):
            p = self.b['parts'][ref]
            pts = [pt for s in p['shapes'] if s[0]=='Line' for pt in s[1:]]
            x,xx=min(pt[0] for pt in pts),max(pt[0] for pt in pts)
            y,yy=min(pt[1] for pt in pts),max(pt[1] for pt in pts)
            self.rect(F,x,y,xx-x,yy-y,.37,dash=True)
            self.inside(F,(x+xx)/2,(y+yy)/2+.68,ref,5.75)
        # The PCB slot below the glass is centered 32 mm above the rear lens.
        self.slot(F,True)
        self.inside(F,self.cx,self.ay+a*.28,'Active display',8,bold=True)
        self.inside(F,self.cx,self.ay+a*.28+3.75,f"{self.p['pixels']} x {self.p['pixels']}",6.5)
        # Complete outer perimeter after any physical graphics on the front.
        for s in self.outer_edges(): self.shape(F,s,.72)

    def outer_edges(self):
        return [s for s in self.b['edges'] if not self.is_slot(s)]

    def is_slot(self,s):
        pts=s[1:] if s[0]=='Line' else s[1]
        return all(abs(p[0]-self.cx)<7.01 and abs(p[1]-(self.cy-32))<2.01 for p in pts)

    def slot(self, face, hidden):
        shapes=[s for s in self.b['edges'] if self.is_slot(s)]
        assert len(shapes)==4, "Camera slot geometry differs from the documented Rev 4 study"
        for s in shapes: self.shape(face,s,.47 if hidden else .65,dash=hidden)

    def rear(self):
        F='B'
        for ref,part in self.b['parts'].items():
            if part['back']: self.fitted(F,part,ref)
        for s in self.outer_edges(): self.shape(F,s,.72)
        # The flat camera neck is 6 mm wide in the Seeed module drawing.
        for x in [self.cx-3,self.cx+3]:
            self.line([self.map(F,(x,self.cy-30)),self.map(F,(x,self.cy-4.25))],.4)
        self.slot(F,False)
        self.rect(F,self.cx-4.25,self.cy-4.25,8.5,8.5,.56,fill=True)
        self.ellipse(F,self.cx,self.cy,2.5,.49)
        self.line([self.map(F,(self.cx-1.55,self.cy)),self.map(F,(self.cx+1.55,self.cy))],.29)
        self.line([self.map(F,(self.cx,self.cy-1.55)),self.map(F,(self.cx,self.cy+1.55))],.29)

        zn=next(v for name,v in self.b['zones'].items() if name.startswith('Jauch 246524'))
        x0,x1=min(x for x,y in zn),max(x for x,y in zn)
        y0,y1=min(y for x,y in zn),max(y for x,y in zn)
        self.rect(F,x0,y0,x1-x0,y1-y0,.64,fill=True)
        self.rect(F,x0+.7,y0+.7,x1-x0-1.4,y1-y0-1.4,.24)
        # Schematic view of the PCM end enclosure from Jauch's pack drawing.
        self.rect(F,x0+1.1,y1-8.9,x1-x0-2.2,8.0,.33)
        xc,yc=(x0+x1)/2,(y0+y1)/2
        self.inside(F,xc,yc-3.0,'Jauch 246524',9.2,bold=True)
        self.inside(F,xc,yc+1.5,'Bonded Li-ion battery',7.4)
        self.inside(F,xc,yc+5.5,'LP735977JH  /  4800 mAh',6.5)
        # Keep the optical axis clear. The exposed rear flex has enough room
        # for its component identity without touching neighbouring components.
        self.inside(F,self.cx-.65,self.cy-16.4,'OV5640 AF camera',6.2,rotate=True)
        return x0,y0,x1,y1

    def draw(self, n):
        F,R='F','B'
        p=self.p
        name='4.0-inch' if p['pixels']==720 else '3.4-inch'
        self.label(12,10.7,'LAB Pocket Computer',17,'left',True)
        self.label(12,15.5,f'{name} panel   /   {p["product"]}   /   {p["panel"]}',8.0,'left')
        self.label(267,10.3,'Rev 4  /  S31 placement R1',8.7,'right',True)
        self.label(267,15.5,f'US Letter   /   1:1   /   {n} of 2',7.4,'right')
        self.label(80,20.7,'Front',9.2,bold=True)
        self.label(203,20.7,'Rear',9.2,bold=True)
        self.front()
        bx,by,bX,bY=self.rear()
        top,bottom=self.top,self.top+self.h
        self.dim_h(self.fr,self.fr+self.w,top-4.5,f'{self.w:.0f}  PCB')
        self.dim_v(top,bottom,self.fr-14,f'{self.h:.0f}  PCB')
        self.dim_v(self.map(F,(0,self.py))[1],self.map(F,(0,self.py+p['height']))[1],self.fr-6,
                   f'{p["height"]:.2f}  panel')
        self.dim_h(self.map(F,(self.px,0))[0],self.map(F,(self.px+p['width'],0))[0],bottom+5.2,f'{p["width"]:.2f}  panel')
        self.dim_h(self.map(F,(self.ax,0))[0],self.map(F,(self.ax+p['active'],0))[0],bottom+10.8,f'{p["active"]:.2f}  active square')
        self.dim_h(self.map(R,(bX,0))[0],self.map(R,(bx,0))[0],bottom+5.2,f'{bX-bx:.2f}  pack max')
        ry1,ry2=self.map(R,(0,by))[1],self.map(R,(0,bY))[1]
        self.dim_v(ry1,ry2,self.rr+self.w+13.8,f'{bY-by:.2f}  pack max')
        self.label(203,top-4.1,'Camera flex slot  14 x 4  /  ends R2',7.0)
        self.label(self.rr+self.w+2,top+2.5,'R2 corners',6.4,align='left')
        self.line([(12,201.9),(20,201.9)],.52)
        self.label(21.4,202.65,'Visible outline',7.1,'left')
        self.line([(46.4,201.9),(54.4,201.9)],.46,dash=True)
        self.label(55.8,202.65,'Hidden camera socket J501, display socket J601 and flex slot',7.1,'left')
        self.label(12,208.25,'Dimensions in mm. Print at 100%. Candidate board outline and folded flex placement.',7.45,'left')
        self.dim_h(240.6,266.0,202.0,'1 inch')
        self.label(253.3,208.25,'Check print scale',7.15)
        self.c.showPage()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--study',type=Path)
    ap.add_argument('--output',type=Path,default=HERE/OUTPUT)
    ap.add_argument('--pcb-python',default=os.environ.get('KICAD_PYTHON','/usr/bin/python3'))
    ap.add_argument('--extract',type=Path,help=argparse.SUPPRESS)
    opts=ap.parse_args()
    if opts.extract:
        print(json.dumps(read_board(opts.extract)))
        return
    from reportlab.lib.pagesizes import landscape,letter
    from reportlab.pdfgen.canvas import Canvas
    study=opts.study or (HERE.parent if (HERE.parent/'source').exists() else HERE.parent/'build')
    panels=json.loads((study/'source'/'panel-envelopes-r1.json').read_text())
    # Use the fixed issue date so regeneration does not alter the printed artifact.
    from datetime import datetime, timezone
    os.environ.setdefault('SOURCE_DATE_EPOCH', str(int(datetime(2026,11,27,12,tzinfo=timezone.utc).timestamp())))
    pdf=Canvas(str(opts.output),pagesize=landscape(letter),pageCompression=1,invariant=1)
    pdf.setTitle('LAB Pocket Computer | ESP32-S31 display fit | R1')
    pdf.setAuthor('LAB Pocket Computer');pdf.setViewerPreference('PrintScaling','None')
    for i,variant in enumerate(('34','40'),1):
        board=next((study/variant).glob('*.kicad_pcb'))
        data=json.loads(subprocess.check_output([opts.pcb_python,str(Path(__file__).resolve()),'--extract',str(board)]))
        Sheet(pdf,panels[variant],data).draw(i)
    pdf.save()


if __name__=='__main__':
    main()
