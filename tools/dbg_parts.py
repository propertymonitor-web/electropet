"""Draw every part of a species in one picture, big, for checking the anatomy:  python3 tools/dbg_parts.py wolf out.png"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_wolf_art as G
from PIL import Image
sp, out = sys.argv[1], sys.argv[2]
so = importlib.import_module("species_organic")
if hasattr(so, "apply_" + sp) and "--old" not in sys.argv:
    getattr(so, "apply_" + sp)(vars(G))
else:
    getattr(importlib.import_module("pet_species"), "apply_" + sp)(vars(G))
name, k, hk, lk = G.STAGES[2]
st = G.Stage(name, k, hk, lk)
tail = int(sys.argv[3]) if len(sys.argv) > 3 else 0
canvas = Image.new("L", (st.cw, st.ch), 0)
def paste(im):
    canvas.paste(255, (0, 0), im)
body = G.BODY if isinstance(G.BODY[0], list) else [G.BODY]
paste(st.render(body))
paste(st.render(G.legs_for_frame(0, lk), leg=True))
paste(st.render(G._pl(G.HEAD_SIDE), head=True))
paste(st.render(G._pl(G.EAR_SIDE[0]), head=True))
tp = G.TAILS[tail][0]
paste(st.render(tp if isinstance(tp[0], list) else [tp]))
canvas.resize((st.cw * 8, st.ch * 8), Image.NEAREST).save(out)
print(out, st.cw, st.ch)
