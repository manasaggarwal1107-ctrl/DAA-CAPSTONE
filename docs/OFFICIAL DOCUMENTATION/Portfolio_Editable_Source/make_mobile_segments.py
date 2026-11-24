from PIL import Image
im=Image.open('assets/screenshots/10-mobile-dashboard.png').convert('RGB')
for s,(a,b) in zip('ABC',[(0,874),(874,1895),(1895,2637)]):
    im.crop((0,a,390,b)).save(f'assets/screenshots/10-mobile-seg{s}.png')
