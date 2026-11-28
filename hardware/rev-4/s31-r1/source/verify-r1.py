#!/usr/bin/env python3
"""Verify KiCad Rev 4 electrical exports against component pinouts and the routed Rev 3A netlist.

    python3 verify-r1.py --baseline r3a.xml net34.xml net40.xml
    /usr/bin/python3 verify-r1.py --baseline r3a.xml --pcb34 34.kicad_pcb net34.xml net40.xml

The checks use independent physical pin tables rather than the schematic generator or its JSON.
They validate electrical connectivity and design calculations. Timing, rail transients, RF behavior,
actual flex mating, mechanical interference and routing require their own verification.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET


class CheckError(ValueError):
    pass


def equal(subject, actual, expected):
    if actual != expected:
        raise CheckError(f'{subject}: expected {expected!r}, got {actual!r}')


class Netlist:
    def __init__(self, path):
        self.path = Path(path)
        xml = ET.parse(path)
        self.parts = {p.get('ref'): p for p in xml.findall('./components/comp')}
        self.pins = defaultdict(dict)
        self.nets = defaultdict(set)
        for net in xml.findall('./nets/net'):
            label = net.get('name')
            if label.startswith('unconnected-'):
                equal(f'{path}: NC net {label} endpoint count', len(net), 1)
                label = None
            for node in net:
                ref, pin = node.get('ref'), node.get('pin')
                if pin in self.pins[ref]:
                    raise CheckError(f'{path}: duplicate node {ref}.{pin}')
                self.pins[ref][pin] = label
                if label is not None:
                    self.nets[label].add((ref, pin))

    def component(self, ref):
        if ref not in self.parts:
            raise CheckError(f'{self.path}: missing component {ref}')
        return self.parts[ref]

    def field(self, ref, key):
        return self.component(ref).findtext(f'fields/field[@name="{key}"]') or ''

    def mpn(self, ref, part):
        equal(f'{ref} MPN', self.field(ref, 'MPN'), part)

    def pins_at(self, ref, mapping):
        self.component(ref)
        for pin, expected in mapping.items():
            actual = self.pins[ref].get(str(pin), '(pin missing)')
            equal(f'{ref}.{pin}', actual, expected)

    def terminals(self, ref, a, b):
        equal(f'{ref} two-terminal nets', set(self.pins[ref].values()), {a, b})
        equal(f'{ref} terminal count', len(self.pins[ref]), 2)


# ESP32-S31 preliminary v0.6, tables 2-1 and 3-1. GPIO29 and GPIO41 are not bonded.
# The actual pads for IO26,27,28,30,31,32 are occupied by external NOR.
GPIO_PADS = dict(zip(
    (*range(26), *range(33, 41), *range(42, 62)),
    (5,6,7,8,9,10,12,13,14,15,16,17,19,20,21,22,23,24,25,26,27,28,29,31,32,33,
     46,47,48,49,50,51,52,53,55,56,57,58,59,60,61,62,65,66,67,68,69,70,71,72,73,74,75,76),
    strict=True,
))
# Espressif hardware-design guide, tables 11 and 12. Bits here are RGB565 logical bit indices.
CONTROLS = {
    0:'PDM_A', 1:'PDM_B', 2:'SYS_SDA', 3:'SYS_SCL', 4:'PDM_CLK', 5:'I2S_MCLK',
    6:'I2S_BCLK', 7:'I2S_LRCLK', 20:'I2S_ADC', 21:'I2S_DAC', 22:'BUS_MISO',
    23:'BUS_MOSI', 24:'BUS_CLK', 25:'RP_CS_N', 37:'SD_INT_CS_N', 38:'IMU_INT',
    39:'RGB_DATA_3V3', 40:'LCD_PCLK', 42:'BL_PWM', 43:'LCD_DE', 44:'LCD_HSYNC',
    45:'LCD_VSYNC', 54:'CAM_PCLK', 55:'CAM_XCLK', 56:'CAM_VSYNC', 57:'CAM_HREF',
    58:'S31_UART0_TX', 59:'HOST_RX', 60:'SD_EXT_CS_N', 61:'HOST_BOOT_N',
}
for prefix, gpios in [('LCD_B', range(8,13)), ('LCD_G', range(13,19)),
                      ('LCD_R', (19,33,34,35,36)), ('CAM_D', range(46,54))]:
    CONTROLS.update({g:f'{prefix}{i}' for i,g in enumerate(gpios)})


def host(n):
    n.mpn('U1', 'ESP32-S31NRV16')
    equal('U1 unique package pads', set(n.pins['U1']), {str(i) for i in range(1,82)})
    equal('GPIO coverage', set(CONTROLS), set(GPIO_PADS))
    n.pins_at('U1', {GPIO_PADS[g]:net for g,net in CONTROLS.items()})
    n.pins_at('U1', {1:'S31_ANT',2:'S31_RF_VDD',3:'S31_RF_VDD',4:'HOST_EN',11:'3V3',
             18:None,30:'S31_PSRAM_1V8',34:'S31_PSRAM_1V8',35:'S31_PSRAM_1V8',39:'HOST_FLASH_VDD',
             43:'3V3',44:'USB_D_P',45:'USB_D_N',54:'3V3',63:'S31_ADC_REF',64:'3V3',77:'3V3',
             78:'HOST_XTAL_N',79:'S31_XTAL_P',80:'3V3',81:'GND'})
    n.mpn('U9','W25Q128JVSIQ')
    for soc,mem,link,line in [(36,1,'R410','CS_N'),(37,2,'R411','D1'),(38,3,'R412','D2'),
                                (40,7,'R413','D3'),(41,6,'R414','CLK'),(42,5,'R415','D0')]:
        local,remote='S31_NOR_'+line,'HOST_NOR_'+line
        n.pins_at('U1',{soc:local}); n.terminals(link,local,remote); n.pins_at('U9',{mem:remote})
        equal(f'{link} NOR tuning',n.component(link).findtext('value'),'0')
    n.pins_at('U9',{4:'GND',8:'HOST_FLASH_VDD'}); n.terminals('R404','HOST_FLASH_VDD','HOST_NOR_CS_N')
    # Boot: strap36 sets 3.3V flash, strap37 JTAG, straps60/61 boot. GPIO45 is a sync signal on S31.
    for ref,net in [('R403','LCD_R4'),('R7','SD_INT_CS_N'),('R11','SD_EXT_CS_N'),
                    ('R402','HOST_BOOT_N'),('R401','HOST_EN')]:
        n.terminals(ref,'3V3',net)
    n.terminals('C424','HOST_EN','GND'); n.terminals('R405','S31_UART0_TX','HOST_TX')
    n.pins_at('J1',{'A6':'USB_D_P','B6':'USB_D_P','A7':'USB_D_N','B7':'USB_D_N'})
    n.pins_at('D22',{1:'USB_D_P',2:'USB_D_N'})
    n.terminals('L402','S31_XTAL_P','HOST_XTAL_P'); n.pins_at('Y1',{1:'HOST_XTAL_P',2:'GND',3:'HOST_XTAL_N',4:'GND'})
    n.terminals('L401','3V3','S31_RF_VDD')
    n.pins_at('U401',{2:'GND',3:'GND',4:'LCD_CS',5:'LCD_SCK',6:'LCD_SDI',7:'LCD_RESET_N',8:'CAM_RESET_N',
            9:'CAM_PWDN',10:'CAM_ANALOG_ENABLE',11:'RP_RUN_N',12:'GND',13:'SD_EXT_DET_N',14:'SD_INT_DET_N',
            21:'3V3',22:'SYS_SCL',23:'SYS_SDA',24:'3V3'})
    n.pins_at('U4',{2:'GND',3:'GND',18:'CAM_ENABLE',21:'GND',22:'SYS_SCL',23:'SYS_SDA'})
    n.pins_at('U2',{33:'RP_SWCLK',34:'RP_SWDIO',35:'RP_RUN_N',66:None,67:None,68:'3V3'})


def display(n, size):
    number,part,geometry = {'34':('5825','TL034WVS05-B1477A','480 x 480'),
                            '40':('5795','TL040HDS20-B1502A','720 x 720')}[size]
    n.mpn('DS601',part)
    equal('physical panel vendor ID',n.field('DS601','vendor_id'),'Adafruit '+number)
    equal('physical panel specification',n.component('DS601').findtext('value'),f'Adafruit {number} / {geometry} non-touch')
    n.mpn('J601','XF2M-4015-1A')
    pins={1:'LCD_LED_A',2:'LCD_LED_K1',3:'LCD_LED_K2',4:'GND',5:'3V3',6:'LCD_RESET_N',
          7:None,8:None,9:'LCD_SDI',10:'LCD_SCK',11:'LCD_CS',12:'LCD_PCLK_FPC',13:'LCD_DE',
          14:'LCD_VSYNC',15:'LCD_HSYNC',16:'GND',28:'GND',34:'GND',40:'GND','MP':None}
    for start,count,prefix in [(17,5,'LCD_B'),(22,6,'LCD_G'),(29,5,'LCD_R')]:
        pins.update({start+i:f'{prefix}{i}' for i in range(count)})
    pins.update({p:None for p in range(35,40)})
    n.pins_at('J601',pins)
    n.terminals('R605','LCD_PCLK','LCD_PCLK_FPC'); n.terminals('R603','LCD_RESET_N','GND'); n.terminals('R604','LCD_CS','3V3')
    n.mpn('U601','TPS61163AYFFR'); n.pins_at('U601',{'A2':'LCD_LED_K2','A3':'LCD_LED_K1','B1':'BL_PWM',
        'A1':'LCD_BL_ISET','B3':'GND','C3':'LCD_BL_SW'})
    n.pins_at('D601',{1:'LCD_LED_A',2:'LCD_BL_SW'}); n.terminals('L601','VSYS','LCD_BL_SW')


def camera(n):
    n.mpn('CAM501','114993115'); n.mpn('J501','AFC01-S24FCC-00')
    # Seeed MJY5OAF-F3M-V1 p.3, written in FLEX contact order, independently of Jushuo PCB numbering.
    flex=[None,'GND','CAM_SDA_1V8','CAM_AVDD_2V8','CAM_SCL_1V8','CAM_RESET_N_1V8','CAM_VSYNC_1V8',
          'CAM_PWDN_1V8','CAM_HREF_1V8','CAM_DVDD_INT','CAM_1V8','CAM_D7_1V8','CAM_XCLK_1V8',
          'CAM_D6_1V8','GND','CAM_D5_1V8','CAM_PCLK_1V8','CAM_D4_1V8','CAM_D0_1V8','CAM_D3_1V8',
          'CAM_D1_1V8','CAM_D2_1V8','GND','CAM_AF_2V8']
    n.pins_at('J501',{25-contact:net for contact,net in enumerate(flex,1)})
    n.pins_at('J501',{25:'GND',26:'GND'})
    equal('sensor internal core bypass only',n.nets['CAM_DVDD_INT'],{('J501','15'),('C501','1'),('C502','1')})
    for ref in ['U503','U504']:
        n.mpn(ref,'SN74AXC8T245PWR')
        n.pins_at(ref,{1:'3V3',12:'GND',13:'GND',22:'CAM_BUS_OE_N',23:'CAM_1V8',24:'CAM_1V8'})
    # TI AXC8 table 7-1: L/L = both B->A. H/H = channels 1..4 A->B, channels 5..8 B->A.
    n.pins_at('U503',{2:'GND',11:'GND'})
    for i in range(8): n.pins_at('U503',{3+i:f'CAM_D{i}',21-i:f'CAM_D{i}_1V8'})
    n.pins_at('U504',{2:'3V3',11:'3V3',3:'CAM_XCLK',21:'CAM_XCLK_DRV_1V8',4:'CAM_PWDN',20:'CAM_PWDN_1V8',
            5:'CAM_RESET_N',19:'CAM_RESET_N_1V8',6:'GND',18:None,7:'CAM_PCLK_DRV',17:'CAM_PCLK_1V8',
            8:'CAM_HREF',16:'CAM_HREF_1V8',9:'CAM_VSYNC',15:'CAM_VSYNC_1V8',10:None,14:'GND'})
    n.terminals('R508','CAM_XCLK_DRV_1V8','CAM_XCLK_1V8'); n.terminals('R509','CAM_PCLK_DRV','CAM_PCLK')
    n.mpn('U505','TCA9406DCUR'); n.pins_at('U505',{1:'SYS_SDA',2:'GND',3:'CAM_1V8',4:'CAM_SDA_1V8',
        5:'CAM_SCL_1V8',6:'CAM_1V8',7:'3V3',8:'SYS_SCL'})
    for ref,mpn,en,out in [('U501','TLV75518PDBVR','CAM_ENABLE','CAM_1V8'),('U502','TLV75728PDBVR','CAM_ANALOG_ENABLE','CAM_2V8')]:
        n.mpn(ref,mpn); n.pins_at(ref,{1:'3V3',2:'GND',3:en,5:out})
    n.terminals('FB501','CAM_2V8','CAM_AVDD_2V8'); n.terminals('FB502','CAM_2V8','CAM_AF_2V8')
    for ref,net,rail in [('R501','CAM_RESET_N_1V8','GND'),('R502','CAM_PWDN_1V8','CAM_1V8'),
                         ('R503','CAM_ENABLE','GND'),('R504','CAM_ANALOG_ENABLE','GND'),('R505','CAM_PWDN','3V3'),
                         ('R506','CAM_RESET_N','GND'),('R507','CAM_BUS_OE_N','3V3')]:
        n.terminals(ref,net,rail)
    n.pins_at('Q501',{1:'CAM_ANALOG_ENABLE',2:'GND',3:'CAM_BUS_OE_N'})


REPLACED_R3A_SHEETS = {
    '/ESP32-P4 local bypass/', '/System clocks and programming pads/', '/IMX219 sensor and camera power/',
    '/LCD logic-level translation/', '/Host compute and radio/', '/ESP32-P4 processor supplies/',
}
REPLACED_IN_RETAINED = {'J2','U20','R48','R49','R50','C64'}


def legacy(original, n):
    original.mpn('U2','RP2350B')
    retained={ref for ref,component in original.parts.items()
              if component.find('sheetpath').get('names') not in REPLACED_R3A_SHEETS and ref not in REPLACED_IN_RETAINED}
    checked=0
    for ref in sorted(retained):
        n.component(ref)
        if ref not in {'R42','R43'}:
            n.mpn(ref,original.field(ref,'MPN'))
        expected=original.pins[ref].copy()
        if ref=='U18': expected['1']='GND'  # Approved revision: forced fixed-frequency PWM.
        equal(f'Rev 3A preserved {ref} pins',n.pins[ref],expected)
        checked+=len(expected)
    # Require all ordinary old subsystems to be present, even with a truncated/wrong baseline.
    for ref in ['U2','U4','U6','U8','U10','U11','U13','U18','U19','U22','U31','U32','J1','J3','J4','Y2',
                *(f'MK{i}' for i in range(1,5)),*(f'SW{i}' for i in range(1,21)),*(f'LED{i}' for i in range(1,33))]:
        if ref not in retained:raise CheckError(f'wrong baseline or retained subsystem missing {ref}')
    return len(retained),checked


def relay_endpoints(original, n):
    # Check that every named P4 application net carried forward still reaches the S31 or new U401.
    preserved={'PDM_A','PDM_B','PDM_CLK','I2S_ADC','I2S_DAC','I2S_BCLK','I2S_LRCLK','I2S_MCLK',
       'BUS_CLK','BUS_MISO','BUS_MOSI','SD_EXT_CS_N','SD_INT_CS_N','RP_CS_N','RP_RUN_N','SYS_SDA','SYS_SCL',
       'IMU_INT','RGB_DATA_3V3','SD_EXT_DET_N','SD_INT_DET_N','BL_PWM','USB_D_P','USB_D_N','HOST_BOOT_N','HOST_EN',
       'HOST_RX','HOST_TX'}
    for net in preserved:
        if net not in original.pins['U1'].values():raise CheckError(f'baseline P4 is missing {net}')
        endpoint='U401' if net in ['SD_EXT_DET_N','SD_INT_DET_N','RP_RUN_N'] else 'U1'
        shared='S31_UART0_TX' if net=='HOST_TX' else net
        if shared not in n.pins[endpoint].values():raise CheckError(f'{net} has no {endpoint} endpoint')


def divider(n):
    n.mpn('U18','TPS63070RNMR'); n.pins_at('U18',{1:'GND',5:'REG_FB',7:'3V3',8:'3V3'})
    n.terminals('R42','REG_FB','GND'); n.terminals('R43','3V3','REG_FB')
    n.mpn('R42','RT0603BRD0710K2L'); n.mpn('R43','RT0603BRD0730K9L')
    def ohms(ref):
        val=n.component(ref).findtext('value'); m=re.fullmatch(r'(\d+(?:\.\d+)?)k',val,re.I)
        if not m:raise CheckError(f'{ref}: unrecognized resistor value {val}')
        return 1000*float(m[1])
    top,bottom=ohms('R43'),ohms('R42');equal('feedback ratio components',(top,bottom),(30900.,10200.))
    nominal=.8*(1+top/bottom)
    # Conservative leakage sign: |I_FB| <= 100 nA. Both divider MPNs are 0.1%.
    lower=.8*.99*(1+top*.999/(bottom*1.001))-100e-9*top*1.001
    upper=.8*1.01*(1+top*1.001/(bottom*.999))+100e-9*top*1.001
    n.terminals('R61','3V3','RP_REG_AVDD'); n.pins_at('U2',{61:'RP_REG_AVDD',68:'3V3'})
    equal('RP analog filter resistance',n.component('R61').findtext('value'),'33R')
    rp_low=lower-.0002*33
    if rp_low<=3.135 or upper>=3.300:raise CheckError(f'shared rail failed: RP {rp_low:.4f}, LCD {upper:.4f} V')
    return nominal,lower,upper,rp_low


def compare(a,b):
    equal('variant references',set(a.parts),set(b.parts))
    for ref in sorted(a.parts):
        ac,bc=a.component(ref),b.component(ref)
        if ref!='DS601':
            equal(f'{ref} same MPN',a.field(ref,'MPN'),b.field(ref,'MPN'))
            equal(f'{ref} same component value',ac.findtext('value'),bc.findtext('value'))
        equal(f'{ref} same footprint',ac.findtext('footprint'),bc.findtext('footprint'))
        equal(f'{ref} same DNP state',ac.find('property[@name="dnp"]') is not None,bc.find('property[@name="dnp"]') is not None)
        equal(f'{ref} pin/net correspondence',a.pins[ref],b.pins[ref])


def pcb_match(netlist,path):
    try:
        import pcbnew
    except ImportError as exc:
        raise CheckError('PCB checking needs KiCad Python bindings (Linux: /usr/bin/python3)') from exc
    board=pcbnew.LoadBoard(str(path)); footprints={f.GetReference():f for f in board.GetFootprints()}
    refs={r for r,p in netlist.parts.items() if p.findtext('footprint')}
    equal('PCB footprint reference set',set(footprints),refs)
    connections=0
    for ref in sorted(refs):
        fp=footprints[ref]; equal(f'PCB {ref} footprint',fp.GetFPIDAsString(),netlist.parts[ref].findtext('footprint'))
        numbers=set()
        for pad in fp.Pads():
            number=pad.GetNumber()
            if not number:continue  # Genuinely unnumbered mechanical/paste primitives.
            numbers.add(number)
            expected=netlist.pins[ref].get(number)
            actual=pad.GetNetname() or None
            if actual and actual.startswith('unconnected-'):actual=None
            equal(f'PCB {ref}.{number} net',actual,expected)
            connections+=1
        missing=set(netlist.pins[ref])-numbers
        if missing:raise CheckError(f'PCB {ref} missing electrical pads: {sorted(missing)}')
    # Both connectors sit on the front. Check actual land order in assembled board coordinates.
    # A swapped/mirrored drawing can have a perfect logical pad-to-net correspondence.
    for ref, count, step, angle in [('J501',24,-0.5,180.), ('J601',40,0.5,0.)]:
        fp=footprints[ref]
        equal(f'{ref} board face', fp.GetLayerName(), 'F.Cu')
        equal(f'{ref} PCB rotation', fp.GetOrientationDegrees()%360, angle)
        positions={p.GetNumber():p.GetPosition() for p in fp.Pads()}
        first=positions['1']
        for num in range(1,count+1):
            pos=positions[str(num)]
            equal(f'{ref}.{num} measured horizontal pitch', pos.x-first.x, pcbnew.FromMM(step*(num-1)))
            equal(f'{ref}.{num} same finger row', pos.y, first.y)
    return f'{len(refs)} footprints, {connections} numbered lands, both FPC row orientations'


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--baseline',type=Path,required=True,help='Rev 3A schematic exported with kicad-cli sch export netlist --format kicadxml')
    parser.add_argument('net34',type=Path);parser.add_argument('net40',type=Path)
    parser.add_argument('--pcb34',type=Path);parser.add_argument('--pcb40',type=Path)
    args=parser.parse_args()
    original,small,large=map(Netlist,[args.baseline,args.net34,args.net40])
    for size,net,pcb in [('34',small,args.pcb34),('40',large,args.pcb40)]:
        retained,pads=legacy(original,net);relay_endpoints(original,net);host(net);display(net,size);camera(net)
        nom,lo,hi,rplo=divider(net)
        print(f'{size}: PASS - {len(net.parts)} refs, {retained} retained Rev 3A components / {pads} terminals; '
              '81 S31 pads, native RGB565/DVP, USB, boot, flash, expander, flex and camera translation.')
        if pcb:print(f'{size} PCB / schematic: PASS - {pcb_match(net,pcb)}.')
    compare(small,large)
    print('Variant comparison: PASS - same electrical connectivity; selected panel MPN and SKU differ.')
    print(f'Shared supply: {nom:.4f} V nominal, {lo:.4f}–{hi:.4f} V static; RP analog pin {rplo:.4f} V lower '
          'estimate at 200 uA. Transient/ripple and physical hardware require measurement.')


if __name__=='__main__':
    try:main()
    except (CheckError,FileNotFoundError,ET.ParseError) as exc:
        sys.exit(f'FAIL: {exc}')
