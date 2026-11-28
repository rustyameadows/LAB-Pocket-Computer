"""Prepare fully independent R2 projects from a delivered S31 R1 study, preserving its electrical UUIDs."""
from argparse import ArgumentParser
from pathlib import Path
import json
import shutil

def prepare(old, new):
    config=json.loads((new/'source/layout-r2.json').read_text())
    panels=json.loads((old/'source/panel-envelopes-r1.json').read_text())
    for size, panel in panels.items():
        margin=(panel['board_width']-panel['width'])/2
        panel.update(screen_pad=round(margin,5),key_pad=config['key_padding'])
        key_height=2*config['key_land_half_height']+(config['rows']-1)*config['row_pitch']
        panel['board_height']=round(margin+panel['height']+2*panel['key_pad']+key_height,5)
        src=old/size;dst=new/size;dst.mkdir(exist_ok=True)
        for p in src.iterdir():
            if p.suffix not in ['.kicad_sch','.kicad_pro','.kicad_sym'] and p.name not in ['sym-lib-table','fp-lib-table']:continue
            name=p.name.replace('-r1','-r2')
            text=p.read_text().replace('S31-'+size+'-r1','S31-'+size+'-r2').replace('S31_'+size+'-r1.kicad_sym','S31_'+size+'-r2.kicad_sym')
            text=text.replace('4 · S31 study R1','4 · S31 layout R2')
            (dst/name).write_text(text)
    (new/'source/panel-envelopes-r2.json').write_text(json.dumps(panels,indent=2)+'\n')
    for folder in ('libraries','datasheets'):
        shutil.copytree(old/folder,new/folder,dirs_exist_ok=True)
if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('r1',type=Path);p.add_argument('r2',type=Path)
    a=p.parse_args();prepare(a.r1,a.r2)
