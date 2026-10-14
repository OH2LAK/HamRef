#!/bin/bash
# usage: route.sh <workdir>   (workdir has parts.json, n.net, hamref.pretty)
set -e
W=$1; HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE" && python3 build_pcb.py "$W" | tail -1
cd "$W"
export_dsn() {
python3 - "$1" <<'PY'
import pcbnew,re
b=pcbnew.LoadBoard(__import__('sys').argv[1]); pcbnew.ExportSpecctraDSN(b,'hamref.dsn')
t=open('hamref.dsn').read()
pw=['3V3','3V3_GNSS','5V_DAC','5V_EXT','5V_MAIN','5V_OCXO','5V_USB','VBUS_MOD','VSYS']
for n in pw: t=re.sub(r'(?<=\s)'+re.escape(n)+r'(?=\s)','',t,count=0) if False else t
m=re.search(r'\(class kicad_default "" ([^(]*)\(circuit',t,re.S)
names=m.group(1).split()
rest=[n for n in names if n not in pw]; pwn=[n for n in names if n in pw]
t=t.replace(m.group(0),'(class kicad_default "" '+' '.join(rest)+'\n      (circuit',1)
t=t.replace('(class Power\n','(class Power '+' '.join(pwn)+'\n',1)
t=t.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)',1)
open('hamref.dsn','w').write(t)
PY
}
SRC=hamref_proto_v0_1.kicad_pcb
for attempt in 1 2 3 4; do
  rm -f hamref.ses
  export_dsn $SRC   # later attempts resume from the previous partial result
  xvfb-run -a java -jar ${FR_JAR:-$HOME/freerouting-1.9.0.jar} -de hamref.dsn -do hamref.ses -mp 40 > fr19.log 2>&1 || true
  R=$(python3 "$HERE/import_ses.py" hamref_proto_v0_1.kicad_pcb hamref.ses routed.kicad_pcb)
  echo "attempt $attempt: $R"
  case "$R" in *"unrouted pairs 0"*) break;; esac
  SRC=routed.kicad_pcb
done
python3 "$HERE/silk_pass.py" routed.kicad_pcb routed.kicad_pcb
python3 - <<'PY'
import pcbnew,re,collections
b=pcbnew.LoadBoard('routed.kicad_pcb'); pcbnew.WriteDRCReport(b,'drc.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)
t=open('drc.rpt').read()
c=collections.Counter(re.findall(r'^\[(\w+)\]',t,re.M)); print(dict(c))
PY
