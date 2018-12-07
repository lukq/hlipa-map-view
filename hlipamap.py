import tkinter
import random
from hmem2 import mr5480

# Hlipa Map Viewer, version 0.6
# December 2018
# by Lukas Petru

# Open source under the MIT License (Expat)

# This program draws a map of Hlipa game world. Hlipa is a game for
# Sharp MZ-800 (8-bit computer).
# Use a keyboard or on-screen buttons to change the floor shown.
# Controls:
# Home/End -show another floor
# c -toggle color/shades of grey rendering
# n -show room numbers

# For Python 3, with Tk 8.6

# Prepares a window with a canvas and scrollbars
c=tkinter.Canvas(name='c',width=400,height=400,sc='0 0 2440 990',highlightt=0,
  xscrollc='.h set',yscrollc='.v set')
tkinter.Scrollbar(name='v',co='.c yview')
tkinter.Scrollbar(name='h',o='h',co='.c xview')

def onKeySym(s):
  e=tkinter.Event(); e.char=e.keysym=s; return lambda:onKey(e)
tkinter.Button(name='u',text='↑',command=onKeySym("Home"))
tkinter.Button(name='d',text='↓',command=onKeySym("End"))

# Decodes Hlipa RAM data
def decodeMem():
  mm=[0]*0xb3a0
  f=r=0;c=1;d=-1
  i=0
  for j in range(1,0xb3a0):
    while c<256:
      a=0
      if f<1:
        if d<0: e=mr5480[i];d=7;i+=1
        f=e>>d&1;d-=1;a=1
        if f<1:
          if d<0: e=mr5480[i];d=7;i+=1
          f=e>>d&1;d-=1;a=2
          if f<1:
            r^=1;c=c*2+r;continue
      f=a;c=c*2+r
      if a>1: r^=1
    mm[j]=c&255;c=1
  return mm[:0x101]+mm[0x81:0x874a]+mm[0x6800:0xb3a0]+mm[0x3b10:0x67a6]

# 64k RAM contents
mm=decodeMem()

# Returns a bitmap as a list {rownum data rownum data ...}
def getBitmap(addr,rows,flip):
  o=''
  for r in range(rows):
    s=''.join(
      'G' if a>>j&1 else '%X'% ((i>>j&1)*8|(g>>j&1)*4|(r>>j&1)*2|b>>j&1)
      for p in range(addr+(rows-r-1)*20,addr+(rows-r)*20,5)
      for a,i,g,r,b in [mm[p:p+5]] for j in range(8))
    o+=' %s '%r+(s[::-1] if flip else s)
  return '{%s}'%o

# Returns a list of tiles {tilename bitmap tilename bitmap ...}
# 1-15 -standard tiles
# 16 -ploxon (0c906)
# 17 19 21 23 -falmon in x+ (0a3d6) x- (0a21e) y+ (0a3d6) y- (0a21e)
# 18 20 22 24 -alternative falmon
# 25 -basic falmon (0a746)
# 26 -falmon halfway up
def getBitmaps():
  b=(0x87ca,21,0, 0x896e,21,0, 0x8b12,21,0, 0x8cb6,21,0, 0x8e5a,21,0,
    0x8ffe,21,0, 0x91a2,21,0, 0x9346,21,0, 0x94ea,21,0, 0x968e,21,0,
    0x9832,21,0, 0x99d6,21,0, 0x9b7a,21,0, 0x9d1e,21,0, 0x9ec2,21,0,
    0xc906,15,0,
    0xa3d6,22,0, 0xa58e,22,0,
    0xa21e,22,0, 0xa066,22,0,
    0xa3d6,22,1, 0xa58e,22,1,
    0xa21e,22,1, 0xa066,22,1,
    0xa746,24,0, 0xa746,24,1)
  return '\n'.join('%s '%(i+1)+getBitmap(*b[3*i:3*i+3]) for i in range(26))

# Use color palette or shades of grey
colorsidx=1
colors=[
  '''0 000 1 00a 2 a00 3 a208aa 4 08a200 5 08a2aa 6 aa0 7 aaa
  8 6e6e6e 9 6e6eff A ff776e B f7f C 77ff6e D 7ff E ffff6e F fff G 000 H eed''',
  '''0 000 1 2e2e2e 2 303030 3 333 4 7a7a7a 5 858585 6 9c9c9c 7 a7a7a7
  8 6e6e6e 9 797979 A 8e8e8e B 999 C ddd D e8e8e8 E fdfdfd F fff G 000 H eee''']

# Image names    Size       Description
# c0-c9, cA-cG   1x1 px     pixel colors
# 1-15           32x21 px   standard tiles
# 16             32x15 px   ploxon
# 17-24          32x22 px   falmon moving x+ x- y+ y-
# 25, 26         32x24 px   basic falmon, falmon moving up

# Creates tile images in Tk from a list of bitmaps
def makeTileImages(bmps):
  c.tk.eval('''lmap {n c} {%s} {[image create photo c$n] put #$c};cG blank
  lmap {n b} {%s} {image create photo $n
    lmap {r v} $b {
      set c -1;foreach v [split $v ""] {$n cop c$v -t [incr c] $r}}}'''%
    (colors[colorsidx],bmps))

# Toggles between colored tiles and grayscale tiles
def toggleColors(e):
  global colorsidx
  colorsidx^=1
  c.tk.eval('.c delete all;.c configure -bg #'+('eee' if colorsidx else 'eed'))
  makeTileImages(getBitmaps())
  show(floor[flooridx],0)

# Sets one point in the voxel array
def point(t,x,y,z):
  if 7<x<16 and 7<y<16: voxel[(z&15)+16*(y-8)+128*(x-8)]=t

def read(cnt):
  global addr,bidx;r=0
  while cnt>=bidx:
    r+=mm[addr]<<(cnt-bidx);cnt-=bidx;addr+=1;bidx=8
  if cnt:
    r+=mm[addr]>>(bidx-cnt);bidx-=cnt
  return r

def rd2(): return read(2)&3
def rd4(): return read(4)&15
def rd16(): return read(16)&65535

def fill(dx,dy,dz,c):
  dx2=rd2()-1;dy2=rd2()-1;dz2=rd2()-1;c2=rd4()+1
  t=rd4();x=rd4();y=rd4();z=rd4()
  for i in range(c):
    for j in range(c2): point(t,x+i*dx+j*dx2,y+i*dy+j*dy2,z+i*dz+j*dz2)

def interp(offset,code):
  global addr,bidx
  olda=addr;oldp=bidx
  addr=0xb36a+code;bidx=8-2*offset
  b=rd2()
  while b<3:
    if b<1: fill(0,0,0,1)
    elif b<2: fill(rd2()-1,rd2()-1,rd2()-1,rd4()+1)
    else: interp(rd2(),rd16())
    b=rd2()
  addr=olda;bidx=oldp

# Fills in the voxel array of the current room
def getVoxels(n):
  voxel[:]=[0]*1024;interp(0,mm[0xd380+8*n]|mm[0xd381+8*n]<<8)

# Puts ploxon into the voxel array
def getPloxon(n):
  for i in range(6):
    if n==mm[0xd36e+3*i]: 
      a=0xd36e+3*i+1;point(16,mm[a]>>4|8,mm[a]&7|8,mm[a+1])

# Falmon movements
# 0  1  2  3  4  5  6  7  8  9  a  b  c  d  e
# x+ x- y+ y- x+ y+ x- y- y+ x- y- x+ z+ z- rnd

# Tests if the place is free for falmon to move in
def free(x,y,z): return voxel[x*128+y*16+z]+voxel[x*128+y*16+z-1]<1

# Puts falmon into the voxel array, returns falmon position
def getFalmon(n):
  if not falmon[n]: return
  x=falmon[n][0];y=falmon[n][1];z=falmon[n][2];b=falmon[n][3]
  a=25  # falmon image
  b=b if b<14 else int(random.uniform(0,12))
  d=0
  for i in range(falmonstep):
    if d: a-=1;d=0;continue
    nx=x+(1,-1,0, 0, 1,0,-1, 0, 0,-1, 0,1, 0, 0)[b]
    ny=y+(0, 0,1,-1, 0,1, 0,-1, 1, 0,-1,0, 0, 0)[b]
    nz=z+(0, 0,0, 0, 0,0, 0, 0, 0, 0, 0,0, 1,-1)[b]
    if 0<=nx<8 and 0<=ny<8 and 0<nz<16 and free(nx,ny,nz):
      x=nx;y=ny;z=nz;a=(18,20,22,24,18,22,20,24,22,20,24,18,26,26)[b];d=1
    else:
      b=(1,0,3,2,5,6,7,4,11,8,9,10,13,12)[b];a=25
      if b==12: z+=1;a=26;d=1
      if b==13: z-=1;a=26;d=1
  y+=(1 if a==24 else 0);x+=(1 if a==20 else 0);z-=(1 if d and b==12 else 0)
  point(a,x|8,y|8,z)
  return (x,y,z-1)

# Draws room tiles that are behind a falmon
def drawBack(xx,yy,zz,r):
  # screen_x = 112 + 16*(x-y); screen_y = 191 - 6*(x+y) - 8*z
  for x in range(7,-1,-1):
    for y in range(7,-1,-1):
      u=112+16*(x-y);v=191-20-6*(x+y)
      for z in range(16 if x>xx or y>yy else zz):
        t=voxel[x*128+y*16+z]
        if t: 
          r+=[u,v-8*z,t]
  return r

# Ploxon and falmon image drawing offsets
offx=[0, 0,-8,0,-8, 0,8,0,8, 0,0]
offy=[-2, 4,7,2,5, 4,7,2,5, 3,-1]

# Draws room tiles that are in front of a falmon
def drawFront(xx,yy,zz,r):
  for x in range(xx,-1,-1):
    for y in range(yy,-1,-1):
      u=112+16*(x-y);v=191-20-6*(x+y)
      for z in range(zz,16):
        t=voxel[x*128+y*16+z]
        if t:
          r+=[u+(0 if t<16 else offx[t-16]),v-8*z+(0 if t<16 else offy[t-16]),t]
  return r

# Draws all tiles of room n
def showRoom(i,update,ox,oy,n):
  if update and not falmon[n]: return (ox,oy,i)
  getVoxels(n);getPloxon(n);f=getFalmon(n) or (7,7,0)
  tiles=drawFront(*f,drawBack(*f,[]))
  c.tk.call('set','m',tiles)
  c.tk.eval('''[image create photo d%s -w 256 -h 192] cop cH -t 0 106 256 192
    lmap {x y t} $m {
      if {$y>=0} {d%s cop $t -t $x $y} {d%s cop $t -t $x 0 -fr 0 [expr {-$y}]}
    }'''%(i,i,i))
  return (ox,oy,i)

def drawNumbers(m):
  c.tk.eval('''lmap {x y t} {%s} {
    .c create r [expr {$x-18}] [expr {$y-10}] [expr {$x+18}] [expr {$y+10}]\
    -f #fff -outline ""
    .c create t $x $y -te $t -fo "Calibri 14"}'''%
    ''.join('%s %s %s '%(x-20,y-63,r) for x,y,r in m))

# Draws rooms of one floor on the canvas
def show(plan,update):
  random.seed(srand)
  c.tk.eval('.c delete all')
  m=[(128+168*(x-y+5),70+63*(x+y-2),plan[y][x])
    for y in range(len(plan)) for x in range(len(plan[y])) if plan[y][x]>-1]
  rooms=[r for i in range(len(m)) for r in showRoom(i,update,*m[i])]
  c.tk.call('set','r',rooms)
  c.tk.eval('''lmap {x y i} $r {.c create i $x $y -i d$i}
   .c create wi 795 934 -win .u; .c create wi 795 970 -win .d
   .c create t 940 970 -te "Floor %s\nPress Home/End to show another floor"'''%
   (flooridx-1))
  if shownumbers: drawNumbers(m)

# Processes keypress event to change the current floor
def onKey(e):
  global flooridx,falmonstep,shownumbers,srand
  if e.keysym=='Home' and flooridx>8 or e.keysym=='End' and flooridx<1: return
  if e.keysym=='Home': flooridx+=1;srand+=1
  if e.keysym=='End': flooridx-=1;srand+=1
  if e.char=='n': shownumbers^=1
  if e.char=='-': falmonstep=(falmonstep+1)%25;show(floor[flooridx],1)
  else: show(floor[flooridx],0)

addr=bidx=0

# Voxel array holding the contents of the currently drawn room
voxel=[]

# Floor plan for each floor
floor=[0]*10

floor[9]=[
[],
[ -1, -1,-1, -1, -1, -1, -1],
[ -1, -1,-1,111, 53,212,140,99],
[ -1, -1,-1,163,201,180, 26,84],
[ -1, -1,-1,120,228,227],
[ -1, -1,-1, 28,114]]

floor[8]=[
[],
[ -1, -1,-1, -1, -1, -1,196],
[ -1, -1,-1,194,134,240, 56, 10],
[ -1, -1,-1, 57,205,254, 14],
[ -1, -1,-1,129,138, 72,233]]

floor[7]=[
[],
[],
[ -1, -1,-1, 88,192,162],
[ -1, -1,-1,131,223,  5,202],
[ -1, -1,-1, 69,145,166, 13],
[],
[],
[ -1, -1,-1, -1,172]]

floor[6]=[
[],
[],
[ -1, -1,-1, 38, -1, -1,203,155,173],
[ -1, -1,-1, 51, 27, 46,  7,190,137,234],
[ -1, -1,-1,  0, 20,133,193,117, 32],
[ -1, -1,18,178,118,200, 33,183],
[ -1, -1,-1,242, 16,164, 66,208],
[ -1, -1,-1,244, 89, 60, 24, 81],
[ -1, -1,-1, -1, -1, -1, 61]]

floor[5]=[
[],
[],
[ -1, -1, -1,116,216,197,246,253],
[ -1, -1, -1,236, 19, 55,198,108,211],
[ -1, -1, -1, 17,241,167,243, 47,151],
[ -1, -1,158,152,125, 91, 37, 74],
[ -1, -1, -1, -1,121,102,128,122, 11],
[ -1, -1, -1, -1,185,229,161,104,217],
[ -1, -1, -1, -1, -1, -1, -1,210]]

floor[4]=[
[ -1, -1,209,157, 22],
[ -1, -1, -1,226,100],
[ -1, -1, -1,174,249,237,250,141, 36,235],
[ -1, -1, -1, 59, 77, 97, 95, 94,119],
[ -1, -1, -1, 93,123,170,135],
[ -1, -1,115, 63,252, 70],
[ -1, -1, -1,126,221,222],
[ -1, -1, -1, 49,207, 75]]

floor[3]=[
[],
[ -1, -1,  1],
[146,130,  6,165,188,248,179,101,40],
[  4,  3,191, 15, 29, 96,175],
[ -1, -1, -1, 62, 65, 98,230],
[ -1, -1, -1, 58,105,218, 64,215],
[ -1, -1, -1,156,  2,142, 30,232],
[ -1, -1, -1, -1,204]]

floor[2]=[
[ -1, -1, -1, -1, -1, -1, -1, -1,169],
[ -1, -1, 44,103, 80, 86, 45, 90,184],
[  8, -1, 79, 87,113,245, 23,159,206],
[149, -1,143, 85, 31, 52, 43,124, 68],
[ -1, -1,107,154, 54,150,247,176,177],
[ -1, -1,106,199,187, 35,136, 83, 76],
[ -1, -1,213,127, 71, 41,182,195,219],
[ -1, -1,168, 50, 73,139, 34,109,231]]

floor[1]=[
[],
[],
[ -1, -1, -1, -1,171],
[ -1, -1, -1, -1,153,132],
[ -1, -1, -1, -1, 25,147]]

floor[0]=[
[],
[ -1, -1, 67, 12,220, 48],
[ -1, -1, 42,160,214,148],
[ -1, -1,  9,144,181, 21],
[ -1, -1,186,112,239,189],
[ -1, -1, -1, -1, -1, -1,225, 78, 39],
[ -1, -1, -1, -1, -1, -1,224,110,238],
[ -1, -1, -1, -1, -1, -1, 92, 82,251]]


shownumbers=0
srand=0
flooridx=6
falmonstep=2
falmon=[0]*255
for i in range(64):
  a=0xf3a7+3*i;falmon[mm[a]]=(mm[a+1]>>4,mm[a+1]&7,mm[a+2]&15,mm[a+2]>>4)

c.tk.eval('''wm title . "Hlípa Map Viewer"
  ttk::copyBindings TtkScrollable Canvas
  grid .c .v -s nsew; grid .h -s ew; grid col . 0 -w 1; grid ro . 0 -w 1''')
c.bind_all('<Home>',onKey)
c.bind_all('<End>',onKey)
c.bind_all('-',onKey)
c.bind_all('n',onKey)
c.bind_all('c',toggleColors)

# Sets the initial position and draws the picture
c.tk.eval('.c xview m .24;.c yview m .15')
toggleColors(0)

tkinter.mainloop()