#!/bin/bash
# Regenerate everything: schematic -> netlist -> PCB (placement + Freerouting) -> docs.
# Needs: KiCad 7 (kicad-cli, pcbnew python), python3 + kiutils + numpy, java + xvfb-run,
#        Freerouting 1.9.0 jar (https://github.com/freerouting/freerouting/releases/tag/v1.9.0): export FR_JAR=/path/freerouting-1.9.0.jar
# NOTE: Freerouting 2.1.0 crashes on this board; use 1.9.0.
# 3D models: stock footprints use ${MODEL_VAR}; default KICAD10_3DMODEL_DIR (export MODEL_VAR=KICAD9_3DMODEL_DIR etc. for other versions).
set -e
T=$(cd "$(dirname "$0")" && pwd); OUT=${1:-$T/../proto-v0.1}
python3 "$T/build.py" "$OUT"                      # schematics + parts.json
(cd "$OUT" && kicad-cli sch export netlist -o n.net hamref_proto_v0_1.kicad_sch)
python3 "$T/erclite.py" "$OUT/n.net"
W=$(mktemp -d); cp -r "$OUT"/* "$W"/
"$T/route.sh" "$W"
cp "$W/routed.kicad_pcb" "$OUT/hamref_proto_v0_1.kicad_pcb"
rm -rf "$OUT/hamref.3dshapes"; cp -r "$W/hamref.3dshapes" "$OUT/"   # simple 3D boxes for OCXO + RP2350-Plus
(cd "$OUT" && kicad-cli pcb export pdf -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,Edge.Cuts -o hamref_proto_v0_1_pcb.pdf hamref_proto_v0_1.kicad_pcb >/dev/null 2>&1; kicad-cli sch export pdf -o hamref_proto_v0_1_schematic.pdf hamref_proto_v0_1.kicad_sch)
python3 "$T/gendoc.py" "$OUT" "$T/../../docs/hardware/proto-v0.1-schematic-plan.md"
rm -f "$OUT/n.net" "$OUT/parts.json"
