from PIL import Image
import os

folder = r"images\nakheel"
for f in os.listdir(folder):
    p = os.path.join(folder, f)
    try:
        img = Image.open(p)
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600), Image.LANCZOS)
            img.save(p, optimize=True, quality=85)
            print("resized", f, img.size)
        else:
            print("ok", f, img.size)
    except Exception as e:
        print("skip", f, e)