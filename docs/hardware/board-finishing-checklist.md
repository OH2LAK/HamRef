# Proto v0.1 - finishing checklist (ERC/DRC and Gerbers)

Do this in KiCad on the Mac (KiCad 10; Freerouting 1.9.0 only needed if you re-run routing).

## 1. ERC (schematic)
1. Open `hardware/proto-v0.1/*.kicad_pro`, Inspection -> Electrical Rules Checker, Run.
2. Expected harmless warnings: unconnected spare GPIOs (GP15-20, GP22) - mark with no-connect flags.
3. Any "pin not driven" on power nets: add PWR_FLAG on the 5 V and 3V3 nets.
4. Fix everything else before layout checks.

## 2. DRC (PCB)
1. Update PCB from schematic (F8) and confirm zero changes.
2. Inspection -> DRC with "Test for parity between PCB and schematic" on. Target: 0 errors.
3. Known open items to resolve:
   - Connector heights vs 15.2 mm usable height inside AKG 105.26 (check every rear-panel connector and the OLED/encoder on the front).
   - USB-C notch/cutout position against the rear panel.
   - Courtyard overlap J3 / U3.
   - Silkscreen text over pads (move or shrink).
   - OCXO footprint: measure the real CTI OSC5A2B02 (pin pitch, drill, body size) before ordering boards.

## 3. Before ordering
- 3D viewer: check clearances against the enclosure and board outline 100 x 80 mm.
- Compare pin 1 and polarity of the GNSS module, OCXO, USB-C and electrolytics with the datasheets.
- Run the schematic's net names against `firmware/src/pins.h`.

## 4. Gerber export
1. File -> Fabrication Outputs -> Gerbers: all copper layers (4), mask, paste, silk, edge cuts; plot format Gerber X2, "Use Protel filename extensions" for most fabs.
2. Generate drill files (Excellon, PTH and NPTH separate, decimal format).
3. Zip, then check with a Gerber viewer (KiCad Gerber Viewer) before upload.
4. Also export BOM and position file (CPL) if the fab assembles.
