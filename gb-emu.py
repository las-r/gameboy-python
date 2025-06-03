import pygame

# made by las-r on github
# v0.2.1

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

# operation functions
def add(num):
    global a
    result = a + num
    clrFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, ((a & 0x0f) + (num & 0x0f)) > 0x0f)
    updFlag(0x10, result > 0xff)
    a = result & 0xff
def adc(num):
    global a
    carry = 1 if isFlag(0x10) else 0
    result = a + num + carry
    clrFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, ((a & 0x0f) + (num & 0x0f) + carry) > 0x0f)
    updFlag(0x10, result > 0xff)
    a = result & 0xff
def sub(num):
    global a
    result = a - num
    setFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, (a & 0x0f) < (num & 0x0f))
    updFlag(0x10, a < num)
    a = result & 0xff
def sbc(num):
    global a
    carry = 1 if isFlag(0x10) else 0
    result = a - num - carry
    setFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, ((a & 0x0f) - (num & 0x0f) - carry) < 0)
    updFlag(0x10, result < 0)
    a = result & 0xff
def and_(num):
    global a
    a = a & num
    updFlag(0x80, a == 0)
    clrFlag(0x40)
    setFlag(0x20)
    clrFlag(0x10)
def xor(num):
    global a
    a = a ^ num
    updFlag(0x80, a == 0)
    clrFlag(0x40 | 0x20 | 0x10)
def or_(num):
    global a
    a = a & num
    updFlag(0x80, a == 0)
    clrFlag(0x40 | 0x20 | 0x10)
def cp(num):
    global a
    result = a - num
    setFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, (a & 0x0f) < (num & 0x0f))
    updFlag(0x10, a < num)

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
        case 3:
            match o1:
                case 0:
                    offset = fetch8()
                    if offset >= 0x10:
                        offset -= 0x100
                    if not isFlag(0x10):
                        pc += offset
                case 1: sp = fetch16()
                case 2: mem[gethl()] = a - 1
                case 3: sp = (sp + 1) & 0xff
                case 4: mem[gethl()] = (mem[gethl()] + 1) & 0xff
                case 5: mem[gethl()] = (mem[gethl()] - 1) & 0xff
                case 6: mem[gethl()] = fetch8()
                case 7:
                    setFlag(0x10)
                    clrFlag(0x40 | 0x20)
                case 8:
                    offset = fetch8()
                    if offset >= 0x80:
                        offset -= 0x100
                    if isFlag(0x10):
                        pc += offset
                case 9: sethl(gethl() + sp)
                case 10: 
                    a = mem[gethl()]
                    sethl(gethl() - 1)
                case 11: sp = (sp - 1) & 0xff
                case 12: a = (a + 1) & 0xff
                case 13: a = (a - 1) & 0xff
                case 14: a = fetch8()
                case 15:
                    updFlag(0x10, not isFlag(0x10))
                    clrFlag(0x40 | 0x20)
        case 4:
            match o1:
                case 0: b = b
                case 1: b = c
                case 2: b = d
                case 3: b = e
                case 4: b = h
                case 5: b = l
                case 6: b = mem[gethl()]
                case 7: b = a
                case 8: c = b
                case 9: c = c
                case 10: c = d
                case 11: c = e
                case 12: c = h
                case 13: c = l
                case 14: c = mem[gethl()]
                case 15: c = a
        case 5:
            match o1:
                case 0: d = b
                case 1: d = c
                case 2: d = d
                case 3: d = e
                case 4: d = h
                case 5: d = l
                case 6: d = mem[gethl()]
                case 7: d = a
                case 8: e = b
                case 9: e = c
                case 10: e = d
                case 11: e = e
                case 12: e = h
                case 13: e = l
                case 14: e = mem[gethl()]
                case 15: e = a
        case 6:
            match o1:
                case 0: h = b
                case 1: h = c
                case 2: h = d
                case 3: h = e
                case 4: h = h
                case 5: h = l
                case 6: h = mem[gethl()]
                case 7: h = a
                case 8: l = b
                case 9: l = c
                case 10: l = d
                case 11: l = e
                case 12: l = h
                case 13: l = l
                case 14: l = mem[gethl()]
                case 15: l = a
        case 7:
            match o1:
                case 0: mem[gethl()] = b
                case 1: mem[gethl()] = c
                case 2: mem[gethl()] = d
                case 3: mem[gethl()] = e
                case 4: mem[gethl()] = h
                case 5: mem[gethl()] = l
                case 6: pass # implement later
                case 7: mem[gethl()] = a
                case 8: a = b
                case 9: a = c
                case 10: a = d
                case 11: a = e
                case 12: a = h
                case 13: a = l
                case 14: a = mem[gethl()]
                case 15: a = a
        case 8:
            match o1:
                case 0: add(b)
                case 1: add(c)
                case 2: add(d)
                case 3: add(e)
                case 4: add(h)
                case 5: add(l)
                case 6: add(mem[gethl()])
                case 7: add(a)
                case 8: adc(b)
                case 9: adc(c)
                case 10: adc(d)
                case 11: adc(e)
                case 12: adc(h)
                case 13: adc(l)
                case 14: adc(mem[gethl()])
                case 15: adc(a)
        case 9:
            match o1:
                case 0: sub(b)
                case 1: sub(c)
                case 2: sub(d)
                case 3: sub(e)
                case 4: sub(h)
                case 5: sub(l)
                case 6: sub(mem[gethl()])
                case 7: sub(a)
                case 8: sbc(b)
                case 9: sbc(c)
                case 10: sbc(d)
                case 11: sbc(e)
                case 12: sbc(h)
                case 13: sbc(l)
                case 14: sbc(mem[gethl()])
                case 15: sbc(a)
        case 10:
            match o1:
                case 0: and_(b)
                case 1: and_(c)
                case 2: and_(d)
                case 3: and_(e)
                case 4: and_(h)
                case 5: and_(l)
                case 6: and_(mem[gethl()])
                case 7: and_(a)
                case 8: xor(b)
                case 9: xor(c)
                case 10: xor(d)
                case 11: xor(e)
                case 12: xor(h)
                case 13: xor(l)
                case 14: xor(mem[gethl()])
                case 15: xor(a)
        case 11:
            match o1:
                case 0: and_(b)
                case 1: and_(c)
                case 2: and_(d)
                case 3: and_(e)
                case 4: and_(h)
                case 5: and_(l)
                case 6: and_(mem[gethl()])
                case 7: and_(a)
                case 8: xor(b)
                case 9: xor(c)
                case 10: xor(d)
                case 11: xor(e)
                case 12: xor(h)
                case 13: xor(l)
                case 14: xor(mem[gethl()])
                case 15: xor(a)
        case 12:
            match o1:
                case 0: or_(b)
                case 1: or_(c)
                case 2: or_(d)
                case 3: or_(e)
                case 4: or_(h)
                case 5: or_(l)
                case 6: or_(mem[gethl()])
                case 7: or_(a)
                case 8: cp(b)
                case 9: cp(c)
                case 10: cp(d)
                case 11: cp(e)
                case 12: cp(h)
                case 13: cp(l)
                case 14: cp(mem[gethl()])
                case 15: cp(a)
                    
    # increment pc
    pc += 1

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
