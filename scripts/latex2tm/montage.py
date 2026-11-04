import sys, glob, subprocess, re
b = sys.argv[1]; per = int(sys.argv[2]) if len(sys.argv) > 2 else 4
fs = sorted(glob.glob(b + '-*.png'), key=lambda f: int(re.search(r'-(\d+)\.png$', f).group(1)))
for k in range(0, len(fs), per):
    subprocess.run(['magick', 'montage'] + fs[k:k+per] + ['-tile', '%dx1' % per, '-geometry', '+4+4', 'M-%s-%d.png' % (b, k // per + 1)], stderr=subprocess.DEVNULL)
print(len(fs))
