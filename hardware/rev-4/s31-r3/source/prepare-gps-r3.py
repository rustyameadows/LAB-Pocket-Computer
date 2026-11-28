"""Create the R3 schematics from R2. Run with the three study directories as arguments."""
from pathlib import Path
import argparse
import re
import runpy
import shutil

def gps_parts():
    pin_table = [
        ('NC','nc'),('3D_FIX','output'),('I2C_SDA','bidir'),('GND','power_in'),
        ('GND','power_in'),('I2C_SCL','bidir'),('EXTINT0','input'),('V_BCKP','power_in'),
        ('VCC','power_in'),*([('GND','power_in')]*6),('RF_OUT','output'),('RF_IN','input'),
        ('GND','power_in'),('GND','power_in'),('JAM_IND','output'),('GND','power_in'),
        ('GND','power_in'),('RESET_N','input'),('GEO_FENCE','output'),('TXD1','output'),
        ('RXD1','input'),('GND','power_in'),('FORCE_ON','input'),('TIMEPULSE','output'),
        ('ANTON','output'),('GND','power_in')]
    nets={'GND':'GND','VCC':'3V3','V_BCKP':'3V3','RF_OUT':'GPS_ANT_OUT','RF_IN':'GPS_RF_IN',
          'TXD1':'GPS_TX_TO_RP','RXD1':'GPS_RX_2V8'}
    parts=[dict(ref='U701',mpn='L96-M33',jlc='C5197298',footprint='RF_GPS:Quectel_L96',
                datasheet='L96-M33-hardware-design-v1.4.pdf',
                pins=[[str(i),name,kind,nets.get(name)] for i,(name,kind) in enumerate(pin_table,1)])]
    passives=[
        ('R701','0','CRCW06030000Z0EA','GPS_ANT_OUT','GPS_RF_IN'),
        ('R702','1k','CRCW06031K00FKEA','RP_TX_TO_GPS','GPS_RX_2V8'),
        ('R703','4.7k','CRCW06034K70FKEA','GPS_RX_2V8','GND'),
        ('C701','10u','C0805C106K4PACTU','3V3','GND'),('C702','100n','C0603C104K5RACTU','3V3','GND'),
        ('C703','4.7u','C0805C475K8PACTU','3V3','GND'),('C704','100n','C0603C104K5RACTU','3V3','GND')]
    for ref,val,mpn,left,right in passives:
        resistor=ref.startswith('R'); package='0805_2012' if mpn.startswith('C0805') else '0603_1608'
        lib='Resistor_SMD:R_' if resistor else 'Capacitor_SMD:C_'
        parts.append(dict(ref=ref,value=val,mpn=mpn,footprint=lib+package+'Metric',
                     datasheet=('CRCW0603' if resistor else mpn)+'.pdf',
                     pins=[['1','1','passive',left],['2','2','passive',right]]))
    return parts

def prepare(r1,r2,dest):
    g=runpy.run_path(str(r1/'source/build-schematics-r1.py'))
    for folder in ('libraries','datasheets'):
        shutil.copytree(r2/folder,dest/folder,dirs_exist_ok=True)
    shutil.copy(r2/'source/panel-envelopes-r2.json',dest/'source/panel-envelopes-r3.json')
    for size in ('34','40'):
        proj=f'LAB-Pocket-S31-{size}-r3'; libname='S31_'+size; d=dest/size;d.mkdir(exist_ok=True)
        for f in (r2/size).iterdir():
            if f.suffix not in ('.kicad_sym','.kicad_sch','.kicad_pro') and f.name not in ('fp-lib-table','sym-lib-table'):continue
            name=f.name.replace('-r2','-r3')
            s=f.read_text().replace(proj[:-1]+'2',proj).replace(f'{libname}-r2',f'{libname}-r3').replace('S31 layout R2','S31 layout R3')
            (d/name).write_text(s)
        rootfile=d/(proj+'.kicad_sch');roottext=rootfile.read_text()
        root=re.search(r'\(uuid ([\w-]+)\)',roottext)[1];name=proj+'-gps';lib={}
        page={'title':'GNSS receiver and RP2350B serial interface','parts':gps_parts(),
              'notes':['U701 uses its internal antenna through R701. Keep both RF runs short.',
                       'UART1 runs at 9600 8N1 by default. GP4 transmits through the divider. GP5 receives NMEA.',
                       'V_BCKP follows the switched system rail. A full power-off loses the retained fix data.']}
        sid=g['draw_parts'](page,name,proj,root,lib,libname,d)
        leaf=d/(name+'.kicad_sch');leaf.write_text(leaf.read_text().replace('S31 study R1','S31 layout R3'))
        libfile=d/(libname+'-r3.kicad_sym')
        libfile.write_text(libfile.read_text().rstrip()[:-1]+'\n'+'\n'.join(lib.values())+')\n')
        x,y=400,309
        sheet=(f'(sheet (at {x} {y}) (size 167 17) (stroke (width .25)(type default)) (fill (type none)) (uuid {sid}) '
               +g['prop']('Sheetname',page['title'],x,y-2,justify='left')+g['prop']('Sheetfile',name+'.kicad_sch',x,y+19,justify='left')
               +f'(instances (project "{proj}" (path "/{root}" (page "28")))))\n'
               +g['text']('Quectel L96, antenna link and serial voltage divider',x+4,y+8.7,1.7,proj+'gps-index'))
        rootfile.write_text(roottext.replace('(embedded_fonts no))',sheet+'\n(embedded_fonts no))'))
        user=d/(proj+'-user-compute.kicad_sch');raw=user.read_text()
        for y,net in [('87.63','RP_TX_TO_GPS'),('90.17','GPS_TX_TO_RP')]:
            pat=rf'\(no_connect \(at 119.38 {re.escape(y)}\) \(uuid [\w-]+\)\)'
            label=(f'(wire (pts (xy 119.38 {y}) (xy 123.19 {y})) (stroke (width 0) (type default)) (uuid {g["uid"](proj+net+"w")}))\n'
                   +f'(global_label "{net}" (shape bidirectional) (at 123.19 {y} 0) {g["effects"](.9,justify="left")} (uuid {g["uid"](proj+net+"l")}))')
            raw,count=re.subn(pat,label,raw);assert count==1
        user.write_text(raw)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('r1','r2','dest'):p.add_argument(arg,type=Path)
    a=p.parse_args();prepare(a.r1,a.r2,a.dest)
