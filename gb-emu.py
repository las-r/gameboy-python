import pygame

# made by las-r on github
# v0.1

# unfinished!!! not functional yet

# pygame init
pygame.init()
pclock = pygame.time.Clock()

# misc
DEBUG = True

# display
WIDTH, HEIGHT = 640, 576
SWIDTH, SHEIGHT = 160, 144
PWIDTH, PHEIGHT = WIDTH // SWIDTH, HEIGHT // SHEIGHT
PALETTE = [(42, 69, 59), 
           (54, 93, 72), 
           (87, 124, 68), 
           (127, 134, 15)]
disp = [[0 for _ in range(SWIDTH)] for _ in range(SHEIGHT)]

# cpu
MC = 4194304
SC = MC // 4

# registers
a = 0
f = 0
b = 0
c = 0
d = 0
e = 0
h = 0
l = 0
pc = 0x0100
sp = 0xfffe
def getaf():
    return (a << 8) | f
def setaf(value):
    global a, f
    a = (value >> 8) & 0xff
    f = value & 0xf0
def getbc():
    return (b << 8) | c
def setbc(value):
    global b, c
    b = (value >> 8) & 0xff
    c = value & 0xff
def getde():
    return (d << 8) | e
def setde(value):
    global d, e
    d = (value >> 8) & 0xff
    e = value & 0xff
def gethl():
    return (h << 8) | l
def sethl(value):
    global h, l
    h = (value >> 8) & 0xff
    l = value & 0xff

# memory
mem = bytearray(0x10000)

# load rom function
def loadRom(path):
    global mem
    with open(path, "rb") as f:
        rom = bytearray(f.read())
    mem[0:0x8000] = rom[:0x8000]
    
    # print title
    if DEBUG:
        print(f"Loaded ROM: {mem[0x134:0x144].decode('ascii', errors='ignore').strip(chr(0))}")

# update screen function
def updScreen():
    for y in range(SHEIGHT):
        for x in range(SWIDTH):
            pygame.draw.rect(screen, PALETTE[disp[y][x]], pygame.Rect(x * PWIDTH, y * PHEIGHT, PWIDTH, PHEIGHT))
    pygame.display.flip()

# fetch value functions
def fetch16():
    global pc
    low = mem[pc]
    pc += 1
    high = mem[pc]
    pc += 1
    return (high << 8) | low
def fetch8():
    global pc
    val = mem[pc]
    pc += 1
    return val

# flag functions
def setFlag(mask):
    global f
    f |= mask
def clrFlag(mask):
    global f
    f &= ~mask
def updFlag(mask, cond):
    global f
    if cond:
        setFlag(mask)
    else:
        clrFlag(mask)
def isFlag(mask):
    return (f & mask) != 0

# execute opcode function
def execOpc(opcode):
    global a, f, b, c, d, e, h, l, pc, sp, mem, disp

    # split into byte chunks
    o0 = (opcode & 0xf0) >> 4
    o1 = opcode & 0x0f

    # execute
    match o0:
        case 0:
            match o1:
                case 1: setbc(fetch16())
                case 2: mem[getbc()] = a
                case 3: setbc(getbc() + 1)
                case 4: b = (b + 1) & 0xff
                case 5: b = (b - 1) & 0xff
                case 6: b = fetch8()
                case 7:
                    carry = (a & 0x80) >> 7
                    a = ((a << 1) | carry) & 0xff
                    clrFlag(0x80 | 0x40 | 0x20)
                    updFlag(0x10, carry == 1)
                case 8:
                    addr = fetch16()
                    pc += 2
                    mem[addr] = sp & 0xff
                case 9: sethl(gethl() + getbc())                    
                case 10: a = mem[getbc()]                    
                case 11: setbc(getbc() - 1)                    
                case 12: c = (c + 1) & 0xff                    
                case 13: c = (c - 1) & 0xff                   
                case 14: c = fetch8()
                case 15:
                    carry = a & 0x01
                    a = ((a >> 1) | (carry << 7)) & 0xff
                    clrFlag(0x80 | 0x40 | 0x20)
                    updFlag(0x10, carry == 1)
        case 1:
            match o1:
                case 0: pass # implement later
                case 1: setde(fetch16())                
                case 2: mem[getde()] = a                
                case 3: setde(getde() + 1)               
                case 4: d = (d + 1) & 0xff                
                case 5: d = (d - 1) & 0xff                
                case 6: d = fetch8()                 
                case 7:
                    ocarry = 1 if isFlag(0x10) else 0
                    carry = (a & 0x80) >> 7
                    a = ((a << 1) | ocarry) & 0xff
                    clrFlag(0x80 | 0x40 | 0x20)
                    updFlag(0x10, carry == 1)                    
                case 8:
                    offset = fetch8()
                    if offset >= 0x80:
                        offset -= 0x100
                    pc += offset
                case 9: sethl(getde() + gethl())                   
                case 10: a = mem[getde()]
                case 11: setde(getde() - 1)
                case 12: e = (e + 1) & 0xff
                case 13: e = (e + 1) & 0xff
                case 14: e = fetch8()
                case 15:
                    ocarry = 1 if isFlag(0x10) else 0
                    carry = a & 0x01
                    a = ((a >> 1) | (ocarry << 7)) & 0xff
                    clrFlag(0x80 | 0x40 | 0x20)
                    updFlag(0x10, carry == 1)
        case 2:
            match o1:
                case 0:
                    offset = fetch8()
                    if offset >= 0x80:
                        offset -= 0x100
                    if not isFlag(0x80):
                        pc += offset
                case 1: sethl(fetch16())
                case 2: mem[gethl()] = a + 1
                case 3: sethl(gethl() + 1)
                case 4: h = (h + 1) & 0xff
                case 5: h = (h - 1) & 0xff
                case 6: h = fetch8()
                case 7:
                    adjust = 0
                    carry = False
                    if not isFlag(0x40):
                        if isFlag(0x10) or a > 0x99:
                            adjust |= 0x60
                            carry = True
                        if isFlag(0x20) or (a & 0x0F) > 9:
                            adjust |= 0x06
                        a = (a + adjust) & 0xFF
                    else:
                        if isFlag(0x10):
                            adjust |= 0x60
                        if isFlag(0x20):
                            adjust |= 0x06
                        a = (a - adjust) & 0xFF
                    clrFlag(0x80)
                    if a == 0:
                        setFlag(0x80)
                    clrFlag(0x20)
                    if isFlag(0x20):
                        setFlag(0x20)
                    if carry:
                        setFlag(0x10)
                    else:
                        clrFlag(0x10)
                case 8:
                    offset = fetch8()
                    if offset >= 0x80:
                        offset -= 0x100
                    if isFlag(0x80):
                        pc += offset
                case 9: sethl(gethl() + gethl())                   
                case 10: 
                    a = mem[gethl()]
                    sethl(gethl() + 1)
                case 11: setde(gethl() - 1)
                case 12: l = (l + 1) & 0xff
                case 13: l = (l + 1) & 0xff
                case 14: l = fetch8()
                case 15:
                    a = a ^ 0xff
                    setFlag(0x40)
                    setFlag(0x20)
                    
    # increment pc
    pc =+ 1

# screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Boy Emulator")

# load rom
loadRom("tetris.gb")

# main run loop
run = True
while run:
    # events
    for event in pygame.event.get():
        # quit event
        if event.type == pygame.QUIT:
            run = False

    # refresh rate
    updScreen()
    pclock.tick(60)

# quit
pygame.quit()
