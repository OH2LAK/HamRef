"""Vectorise the HamREF logo (text + satellite) from the enclosure mockup into silk polygons.
Usage: make_logo.py <mockup.jpg> -> logo/hamref_logo.json (polygons in px, with holes) + logo/hamref_logo_preview.png"""
import sys, json, cv2, numpy as np
src = sys.argv[1]
im = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
x0, y0, x1, y1 = 238, 419, 905, 705        # crop of the front panel logo (original 2048x2048 coordinates)
c = im[y0:y1, x0:x1]
# the panel is brushed aluminium: remove the slowly varying background, then threshold dark ink
bg = cv2.GaussianBlur(c, (0, 0), 25)
d = cv2.subtract(bg, c)
_, bw = cv2.threshold(d, 38, 255, cv2.THRESH_BINARY)
bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
cv2.imwrite('logo/hamref_logo_preview.png', 255 - bw)
cnts, hier = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
out = []
for i, cn in enumerate(cnts):
    if cv2.contourArea(cn) < 12: continue
    ap = cv2.approxPolyDP(cn, 0.7, True)[:, 0, :].tolist()
    if len(ap) < 3: continue
    out.append({'id': i, 'pts': ap, 'hole': bool(hier[0][i][3] >= 0), 'parent': int(hier[0][i][3])})
json.dump({'w': x1 - x0, 'h': y1 - y0, 'contours': out}, open('logo/hamref_logo.json', 'w'))
print(len(out), 'contours', bw.shape)
