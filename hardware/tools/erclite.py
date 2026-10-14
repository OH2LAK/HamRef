import re, os, sys
t=open(sys.argv[1]).read(); base=os.path.dirname(sys.argv[1])
nets=re.findall(r'\(net \(code "\d+"\) \(name "([^"]*)"\)((?:\s*\(node [^\n]*)+)',t)
single=[];unc=[]
conn=0
for name,body in nets:
    nodes=re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "([^"]*)"\))?(?: \(pintype "([^"]*)"\))?',body)
    if name.startswith('unconnected'): unc+=[(name,n) for n in nodes]; continue
    if len(nodes)==1: single.append((name,nodes[0]))
    # driver check: nets with only inputs/passive
    types={n[3] for n in nodes}
    if name not in('GND',) and len(nodes)>1 and types<= {'input'}: print('  no driver:',name)
print('nets',len(nets))
print('SINGLE-NODE NETS:'); [print('  ',n,x[0],x[1],x[2]) for n,x in single]
print('UNCONNECTED non-NC pins:')
for name,n in unc:
    pf=n[2]
    print('  ',n[0],n[1],pf,n[3]) if (n[3] in('power_in','power_out','input','output','bidirectional') ) else None
fps=set(re.findall(r'\(footprint "([^"]*)"\)',t))
for f in sorted(fps):
    if not f: print('EMPTY footprint'); continue
    lib,n=f.split(':')
    p=f'/usr/share/kicad/footprints/{lib}.pretty/{n}.kicad_mod' if lib!='HamREF' else f'{base}/hamref.pretty/{n}.kicad_mod'
    if not os.path.exists(p): print('MISSING FP',f)
