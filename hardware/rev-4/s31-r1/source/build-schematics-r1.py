"""Recreate Rev 4 R1 schematic files from the committed Rev 3A and electrical definitions."""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import uuid

KEYS = ("host", "camera")
BASE = "LAB-Pocket-R3A"
LEGACY_SHEETS = {
    "R3-keypad": "Key matrix and scan port", "R3-key-pixels": "Key illumination", "R3-lighting": "Perimeter LEDs",
    "R3-panel-storage": "Dual microSD", "R3-user-compute": "RP2350B user processor", "R3-support-rp": "RP2350B supplies and memory",
    "R3-sensing": "Audio connectors and IMU", "R3A-support-audio": "Stereo codec and amplifier",
    "R3-support-imu-strap": "IMU address", "R3-power": "Battery and USB connector", "R3-support-battery": "Charge interlock and gauge",
    "R3-support-usb": "Type-C current detection", "R3-support-regulators": "System voltage regulator",
    "R3-support-led-drive": "Pixel boost supply", "R3-support-power-entry": "Supply entry points",
}
DROP = {"R3-panel-storage": {"J2"}, "R3-support-led-drive": {"U20","R48","R49","R50","C64"}, "R3-support-power-entry":{"#FLG03"}}
NOTES = {
    "03   /   DISPLAY  /  STORAGE":"DUAL microSD",
    "TTC273XSI-01":"Two independent card selects share the host SPI bus with the user processor.",
    "U26 supplies":None, "Two active sinks":None,
    "LED supply and display backlight":"Pixel boost supply",
    "U4 P0.4 enables":"U4 P0.4 enables the 5 V pixel boost.",
    "Power enters through":"VBUS enters at J1. L4 supplies the RP core. R61 feeds its analog regulator supply.",
    "U31 supplies microphone bias":"U31 supplies microphone bias and headphone drive. U32 drives the two spring-contact speakers.",
}
def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "lab-pocket-r4-r1/" + name))
def q(value):
    return json.dumps(str(value),ensure_ascii=False)
def n(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") or "0"
def effects(size=1, hide=False, justify=None):
    return f'(effects (font (size {size} {size}))' + (f' (justify {justify})' if justify else '') + (' (hide yes)' if hide else '') + ')'
def prop(k,v,x,y,hide=False,justify=None):
    return f'(property {q(k)} {q(v)} (at {n(x)} {n(y)} 0) {effects(1.1,hide,justify)})'
def text(t,x,y,size,key):
    return f'(text {q(t)} (at {n(x)} {n(y)} 0) {effects(size,justify="left")} (uuid {uid(key)}))'
def page_start(title,pageid,paper="A3"):
    return f'(kicad_sch (version 20260101) (generator eeschema) (uuid {pageid}) (paper "{paper}") (title_block (title {q(title)}) (rev "4 · S31 study R1") (company "LAB Pocket Computer"))'
def filter_leaf(raw, stem):
    """Compact Rev 3A files group each instance and its generated terminal wires together."""
    active=True
    output=[]
    for line in raw.splitlines():
        if line.startswith('(symbol (lib_id'):
            active=re.search(r'\(property "Reference" "([^"]+)"',line)[1] not in DROP.get(stem,set())
        elif line.startswith(("(text ","(embedded_fonts")):
            active=True
        if not active: continue
        if line.startswith("(text "):
            match=re.search(r'^\(text "([^"]+)"',line)
            prefix=next((key for key in NOTES if match[1].startswith(key)),None)
            if prefix:
                if NOTES[prefix] is None: continue
                line=line.replace(q(match[1]),q(NOTES[prefix]),1)
        if stem=='R3-support-regulators' and line.startswith('(symbol (lib_id'):
            for ref,oldval,newval,oldid,newid in [('R43','309k','30.9k','CRCW0603309KFKEA','RT0603BRD0730K9L'),('R42','100k','10.2k','CRCW0603100KFKEA','RT0603BRD0710K2L')]:
                if '(property "Reference" "'+ref+'"' in line:
                    line=line.replace(q(oldval),q(newval)).replace(q(oldid),q(newid)).replace('datasheets/CRCW0603.pdf','datasheets/'+newid+'.pdf')
        if stem=='R3-support-regulators' and '5d1b008b-2c0e-548b-b7d3-315bcb76d7fa' in line:
            line=line.replace('"VSYS"','"GND"')
        output.append(line)
    out='\n'.join(output)+'\n'
    out=re.sub(r'\(rev "[^"]+"\)', '(rev "4 · S31 study R1")',out,count=1)
    return re.sub(r'\(title "[^"]+"\)',f'(title {q(LEGACY_SHEETS[stem])})',out,count=1)
def label_net(name):
    return {" +3V3":"3V3","+3V3":"3V3","+3.3V":"3V3"}.get(name,name)
def part_symbol(part):
    pins=part['pins']; ref=part['ref']
    simple=bool(re.fullmatch(r'[RCL][0-9]+',ref)) and len(pins)==2
    ports=[];body=3.81 if simple else 17.78
    count=math.ceil(len(pins)/2)
    h=1.27 if simple else (count+1)*1.27
    symbol_name="Part_"+ref
    if simple:
        if ref[0]=='C':
            shapes=''.join(f'(polyline (pts (xy {x} -1.8) (xy {x} 1.8)) (stroke (width 0.34) (type default))(fill (type none)))' for x in [-0.55,0.55])
            for s in [-1,1]:shapes+=f'(polyline (pts (xy {s*body} 0) (xy {s*.55} 0)) (stroke (width 0.18) (type default))(fill (type none)))'
        elif ref[0]=='R':
            shapes=f'(rectangle (start {-body} 1.25) (end {body} -1.25) (stroke (width 0.23) (type default))(fill (type none)))'
        else:
            shapes=''.join(f'(arc (start {n(-body+i*1.905)} 0) (mid {n(-body+i*1.905+.9525)} .9525) (end {n(-body+(i+1)*1.905)} 0) (stroke (width 0.2) (type default))(fill (type none)))' for i in range(4))
    else: shapes=f'(rectangle (start {-body} {h}) (end {body} {-h}) (stroke (width 0.23) (type default))(fill (type background)))'
    name_clause='(pin_names (offset 0.7)'+(' (hide yes)' if simple else '')+')'
    out=[f'(symbol "{symbol_name}" {name_clause}'+(' (pin_numbers (hide yes))' if simple else '')+' (in_bom yes) (on_board yes)',prop('Reference',re.sub('[0-9]+','',ref),0,h+5),prop('Value',part.get('value') or part['mpn'],0,h+2),f'(symbol "{symbol_name}_0_1" {shapes})',f'(symbol "{symbol_name}_1_1"']
    for i,(number,name,kind,net) in enumerate(pins):
        left=i<count; side=-1 if left else 1
        x=side*(body+2.54); y=0 if simple else h-2.54*((i%count)+1)
        kind={"bidir":"bidirectional","power_input":"power_in","power_output":"power_out","nc":"no_connect"}.get(kind,kind)
        if kind not in 'input output bidirectional tri_state passive free unspecified power_in power_out open_collector open_emitter no_connect'.split():raise ValueError((ref,kind))
        out.append(f'(pin {kind} line (at {n(x)} {n(y)} {0 if left else 180}) (length 2.54) (name {q(name)} {effects(.85)}) (number {q(number)} {effects(.8)}))')
        ports.append((x,y,left,label_net(net),kind))
    return symbol_name,'\n'.join(out)+'))',ports,h

def draw_parts(page, name, proj, root, lib, libname, location):
    sid=uid(proj+'/'+name+'/instance')
    pieces=[]; symbols={}; x0=66.04; ytop=35.56; row_h=0; col=0
    caption=page['title']; count=0
    for part in page['parts']:
        key,raw,ports,h=part_symbol(part); ref=part['ref']; symid=libname+':'+key
        if key in lib and lib[key]!=raw:raise ValueError('inconsistent definition '+key)
        lib[key]=raw; symbols[key]=raw.replace(f'(symbol "{key}"',f'(symbol "{symid}"',1)
        if col>=3:
            col=0; ytop+=row_h; row_h=0
        x=x0+col*129.54; y=round((ytop+h+6.35)/1.27)*1.27
        row_h=max(row_h,2*h+18); col+=1; count+=1
        val=part.get('value') or part['mpn']; loc=part.get("local_datasheet") or part.get("datasheet") or ""; fp=part.get("footprint") or ""
        if loc and not loc.startswith(("http","$")):loc="${KIPRJMOD}/../datasheets/"+Path(loc).name
        props=prop('Reference',ref,x,y-h-5)+prop('Value',val,x,y-h-2.8)+prop('Footprint',fp,x,y,True)+prop('Datasheet',loc,x,y,True)+prop('MPN',part['mpn'],x,y,True)
        for k in ('jlc','lcsc','assembly','vendor_id'):
            if part.get(k):props+=prop({'lcsc':'LCSC','jlc':'LCSC'}.get(k,k),part[k],x,y,True)
        dnp=' (dnp yes)' if part.get('dnp') else ''
        symuid=uid(proj+'/component/'+ref)
        pieces.append(f'(symbol (lib_id {q(symid)}) (at {n(x)} {n(y)} 0) (unit 1){dnp} (in_bom yes) (on_board {"yes" if fp else "no"}) (uuid {symuid}) {props} (instances (project {q(proj)} (path "/{root}/{sid}" (reference {q(ref)}) (unit 1)))))')
        for i,(dx,dy,left,net,kind) in enumerate(ports):
            a=x+dx;b=y-dy;e=a+(-5.08 if left else 5.08); k=proj+'/'+ref+'/'+str(i)
            if net is None or net is False:
                if kind!='no_connect':pieces.append(f'(no_connect (at {n(a)} {n(b)}) (uuid {uid(k+"nc")}))')
                continue
            pieces.extend((f'(wire (pts (xy {n(a)} {n(b)}) (xy {n(e)} {n(b)})) (stroke (width 0) (type default)) (uuid {uid(k+"w")}))',
                f'(global_label {q(net)} (shape bidirectional) (at {n(e)} {n(b)} {180 if left else 0}) {effects(.85,justify="right" if left else "left")} (uuid {uid(k+"g")}))'))
    notes=page.get('notes',[])
    note_y=ytop+row_h+5
    paper='A3' if note_y+6*len(notes)<260 else ('A2' if note_y+6*len(notes)<390 else 'A1')
    if note_y+6*len(notes)>555:raise ValueError(f'Split sheet {name}: too many parts')
    for j,line in enumerate(notes):
        pieces.append(text(line,16,note_y+5*j,1.3,proj+name+'note'+str(j)))
    hdr=text(caption,16,17,3.3,proj+name+'heading')
    (location/(name+'.kicad_sch')).write_text(page_start(caption,uid(proj+'/'+name),paper)+' (lib_symbols\n'+'\n'.join(symbols.values())+')\n'+hdr+'\n'+'\n'.join(pieces)+'\n(embedded_fonts no))\n')
    return sid

def render(base,out,variant,definitions):
    proj='LAB-Pocket-S31-'+variant+'-r1'; libname='S31_'+variant; dest=out/variant
    dest.mkdir(exist_ok=True,parents=True);lib={}; root=uid(proj); sheets=[]
    legacy_root=(base/(BASE+'.kicad_sch')).read_text()
    oldroot=re.search(r'\(uuid ([\w-]+)\)',legacy_root)[1]
    for page in definitions:
        name=proj+'-'+page['key'].lower().replace('_','-'); sid=draw_parts(page,name,proj,root,lib,libname,dest)
        sheets.append((name,page['title'],sid))
    for stem,title in LEGACY_SHEETS.items():
        name=proj+'-'+stem.split('-',1)[1]
        line=next(l for l in legacy_root.splitlines() if l.startswith('(sheet ') and '"'+stem+'.kicad_sch"' in l)
        sid=re.search(r'\(uuid ([\w-]+)\)',line)[1]
        leaf=filter_leaf((base/(stem+'.kicad_sch')).read_text(),stem).replace(BASE,proj).replace('/'+oldroot+'/', '/'+root+'/')
        if stem=='R3-support-power-entry':
            # Duplicate two real external-feed flags onto passive-filter outputs.
            group=re.search(r'^\(symbol \(lib_id "power:PWR_FLAG".*?"#FLG01".*?$\n^\(wire .*?$\n^\(global_label "VBUS" .*?$',leaf,re.M)
            if not group:raise ValueError("Missing power-entry template")
            for index,(net,ref) in enumerate([('S31_RF_VDD','#FLG041'),('LCD_BL_VIN','#FLG061')]):
                block=group[0].replace('#FLG01',ref).replace('"VBUS"',q(net))
                block=re.sub(r'\(uuid ([\w-]+)\)',lambda m:'(uuid '+uid(proj+ref+m[1])+')',block)
                dx=76.2*index;dy=50.8
                block=re.sub(r'\((at|xy) ([-.\d]+) ([-.\d]+)',lambda m:f'({m[1]} {n(float(m[2])+dx)} {n(float(m[3])+dy)}',block)
                leaf=leaf.replace('\n(embedded_fonts no))','\n'+block+'\n(embedded_fonts no))')
        (dest/(name+'.kicad_sch')).write_text(leaf)
        sheets.append((name,title,sid))
    parts=[page_start(proj,root,'A2')+' (lib_symbols)',text('LAB Pocket Computer',18,20,4.6,proj+'title'),
           text(('4-inch   /   720 × 720   /   Adafruit 5795' if variant=='40' else '3.4-inch   /   480 × 480   /   Adafruit 5825')+'   ·   RGB565   ·   Seeed OV5640 autofocus',18,33,2.1,proj+'caption')]
    for i,(name,title,sid) in enumerate(sheets):
        x=20+(i%3)*190; y=53+(i//3)*32
        parts.append(f'(sheet (at {x} {y}) (size 167 17) (stroke (width .25)(type default)) (fill (type none)) (uuid {sid}) '+prop('Sheetname',title,x,y-2,justify='left')+prop('Sheetfile',name+'.kicad_sch',x,y+19,justify='left')+f'(instances (project {q(proj)} (path "/{root}" (page "{i+2}")))))')
    (dest/(proj+'.kicad_sch')).write_text('\n'.join(parts+['(embedded_fonts no))\n']))
    (dest/(libname+'-r1.kicad_sym')).write_text('(kicad_symbol_lib (version 20251024) (generator kicad_symbol_editor)\n'+'\n'.join(lib.values())+')\n')
    (dest/'sym-lib-table').write_text(f'(sym_lib_table (version 7) (lib (name "LAB")(type "KiCad")(uri "${{KIPRJMOD}}/../libraries/LAB-r1.kicad_sym")(options "")(descr "")) (lib (name "{libname}")(type "KiCad")(uri "${{KIPRJMOD}}/{libname}-r1.kicad_sym")(options "")(descr "")))\n')
    (dest/'fp-lib-table').write_text('(fp_lib_table (version 7) '+''.join(f'(lib (name "{label}")(type "KiCad")(uri "${{KIPRJMOD}}/../libraries/{label}-r1.pretty")(options "")(descr ""))' for label in ['LAB','LABR4'])+')\n')
    pro=json.loads((base/(BASE+'.kicad_pro')).read_text().replace(BASE,proj))
    for field in ['classes','netclass_patterns']:
        pro['net_settings'][field]=[c for c in pro['net_settings'][field] if c.get('name',c.get('netclass'))!='MIPI CSI' and c.get('pattern')!='P4_CORE']
    (dest/(proj+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('rev3a',type=Path); parser.add_argument('destination',type=Path);a=parser.parse_args()
    src=Path(__file__).resolve().parent; out=a.destination; base=a.rev3a/'kicad'; libs=out/'libraries'; libs.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(base/'LAB.kicad_sym',libs/'LAB-r1.kicad_sym')
    for f in (base/'LAB.pretty').glob('*.kicad_mod'):
        if f.stem.startswith(('DF37','ESP32','Touch','VEML')):continue
        dest=libs/'LAB-r1.pretty'/f.name;dest.parent.mkdir(exist_ok=True)
        dest.write_text(f.read_text().replace('/models-v5/','/../libraries/models-v5/'))
    shutil.copytree(base/'models-v5',libs/'models-v5',dirs_exist_ok=True)
    for variant in ('34','40'):
        data=[]
        for key in (*KEYS,'panel'+variant):
            data+=json.loads((src/(key+'-r1.json')).read_text())['pages']
        render(base,out,variant,data)
if __name__=='__main__':main()
