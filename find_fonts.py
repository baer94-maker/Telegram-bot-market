import os

search_dirs = [
    "/system/fonts",
    "/system/font", 
    "/system/product/fonts",
]

found = []
for d in search_dirs:
    try:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith((".ttf", ".ttc", ".otf")):
                    found.append(os.path.join(d, f))
    except Exception as e:
        print(f"Папка {d}: {e}")

if found:
    for f in sorted(found):
        print(f)
else:
    print("Шрифты не найдены")