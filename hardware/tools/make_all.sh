#!/bin/bash
# Regenerate everything: schematic -> netlist -> PCB (placement + Freerouting) -> docs.
# Needs: KiCad 7 (kicad-cli, pcbnew python), python3 + kiutils + numpy, java + xvfb-run,
#        Freerouting 1.9.0 jar (https://github.com/freerouting/freerouting/releases/tag/v1.9.0): export FR_JAR=/path/freerouting-1.9.0.jar
# NOTE: Freerouting 2.1.0 crashes on this board; use 1.9.0.
set -e
T=$(cd "$(dirname "$0")" && pwd); OUT=${1:-$T/../proto-v0.1}
python3 "$T/build.py" "$OUT"                      # schematics + parts.json
(cd "$OUT" && kicad-cli sch export netlist -o n.net hamref_proto_v0_1.kicad_sch)
python3 "$T/erclite.py" "$OUT/n.net"
W=$(mktemp -d); cp -r "$OUT"/* "$W"/
"$T/route.sh" "$W"
cp "$W/routed.kicad_pcb" "$OUT/hamref_proto_v0_1.kicad_pcb"
(cd "$OUT" && kicad-cli sch export pdf -o hamref_proto_v0_1_schematic.pdf hamref_proto_v0_1.kicad_sch)
python3 "$T/gendoc.py" "$OUT" "$T/../../docs/hardware/proto-v0.1-schematic-plan.md"
rm -f "$OUT/n.net" "$OUT/parts.json"
