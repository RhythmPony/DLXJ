import os
import shutil

if not os.path.exists("./src/BAK"):
    os.mkdir("./src/BAK")

for py in os.listdir("./src"):
    if py.endswith(".py"):
        if not ("DLXJResources_rc" in py):
            shutil.move(os.path.join("./src", py), os.path.join("./src/BAK", py))
        else:
            shutil.copy(os.path.join("./src", py), os.path.join("./src/BAK", py))

for byd in os.listdir("."):
    if byd.endswith(".pyd"):
        new_name = byd.split('.')[0] + '.' + byd.split('.')[-1]
        if not ("base.pyd" == new_name):
            shutil.move(byd, os.path.join("src", new_name))
        else:
            os.rename(byd, new_name)

for c in os.listdir("./src"):
    if c.endswith(".c"):
        os.remove(os.path.join("./src", c))

if os.path.exists("base.c"):
    os.remove("base.c")
