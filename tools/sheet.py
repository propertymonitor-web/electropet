"""Put several species pictures from dbg_parts.py on one sheet:  python3 tools/sheet.py out.png prefix name name ..."""
import sys
from PIL import Image, ImageDraw
out, prefix, names = sys.argv[1], sys.argv[2], sys.argv[3:]
ims = [(n, Image.open("%s%s.png" % (prefix, n))) for n in names]
W = max(i.width for _, i in ims) // 2; H = max(i.height for _, i in ims) // 2
cols = 4; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * (H + 14)), (0, 0, 0))
d = ImageDraw.Draw(sheet)
for k, (n, im) in enumerate(ims):
    im = im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    x = (k % cols) * W; y = (k // cols) * (H + 14)
    sheet.paste(im.convert("RGB"), (x, y + 14)); d.text((x + 3, y + 1), n, fill=(120, 200, 255))
sheet.save(out); print(out, sheet.size)
