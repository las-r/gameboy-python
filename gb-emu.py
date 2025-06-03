import pygame

# made by las-r on github
# v0.4

# unfinished!!! not functional yet

# to do:
# finish interrupting instructions
# make the actual instruction-running loop

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

# stack functions
def pop16():
    global sp
    low = mem[sp]
    high = mem[sp + 1]
    sp += 2
    return (high << 8) | low
def push16(val):
    global sp
    sp -= 2
    mem[sp] = val & 0xFF
    mem[sp + 1] = (val >> 8) & 0xFF

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
def add(a, num):
    result = a + num
    clrFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, ((a & 0x0f) + (num & 0x0f)) > 0x0f)
    updFlag(0x10, result > 0xff)
    a = result & 0xff
    return a
def adc(a, num):
    carry = 1 if isFlag(0x10) else 0
    result = a + num + carry
    clrFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, ((a & 0x0f) + (num & 0x0f) + carry) > 0x0f)
    updFlag(0x10, result > 0xff)
    a = result & 0xff
    return a
def sub(a, num):
    result = a - num
    setFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, (a & 0x0f) < (num & 0x0f))
    updFlag(0x10, a < num)
    a = result & 0xff
    return a
def sbc(a, num):
    carry = 1 if isFlag(0x10) else 0
    result = a - num - carry
    setFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, ((a & 0x0f) - (num & 0x0f) - carry) < 0)
    updFlag(0x10, result < 0)
    a = result & 0xff
    return a
def and_(a, num):
    a = a & num
    updFlag(0x80, a == 0)
    clrFlag(0x40)
    setFlag(0x20)
    clrFlag(0x10)
    return a
def xor(a, num):
    a = a ^ num
    updFlag(0x80, a == 0)
    clrFlag(0x40 | 0x20 | 0x10)
    return a
def or_(a, num):
    a = a & num
    updFlag(0x80, a == 0)
    clrFlag(0x40 | 0x20 | 0x10)
    return a
def cp(a, num):
    result = a - num
    setFlag(0x40)
    updFlag(0x80, (result & 0xff) == 0)
    updFlag(0x20, (a & 0x0f) < (num & 0x0f))
    updFlag(0x10, a < num)
    return a

# cb operation functions
def rlc(val):
    carry = (val >> 7) & 1
    result = ((val << 1) | carry) & 0xFF
    setFlag(Z=(result == 0), N=0, H=0, C=carry)
    return result
def rrc(val):
    carry = val & 1
    result = ((carry << 7) | (val >> 1)) & 0xFF
    setFlag(Z=(result == 0), N=0, H=0, C=carry)
    return result
def rl(val):
    carry_in = isFlag(0x01)
    carry_out = (val >> 7) & 1
    result = ((val << 1) | carry_in) & 0xFF
    setFlag(Z=(result == 0), N=0, H=0, C=carry_out)
    return result
def rr(val):
    carry_in = isFlag(0x01)
    carry_out = val & 1
    result = ((carry_in << 7) | (val >> 1)) & 0xFF
    setFlag(Z=(result == 0), N=0, H=0, C=carry_out)
    return result
def sla(val):
    carry = (val >> 7) & 1
    result = (val << 1) & 0xFF
    setFlag(Z=(result == 0), N=0, H=0, C=carry)
    return result
def sra(val):
    carry = val & 1
    result = (val >> 1) | (val & 0x80)  # keep MSB
    setFlag(Z=(result == 0), N=0, H=0, C=carry)
    return result
def srl(val):
    carry = val & 1
    result = val >> 1
    setFlag(Z=(result == 0), N=0, H=0, C=carry)
    return result
def swap(val):
    result = ((val & 0x0F) << 4) | ((val & 0xF0) >> 4)
    setFlag(Z=(result == 0), N=0, H=0, C=0)
    return result
def bit(val, n):
    setFlag(Z=((val >> n) & 1) == 0, N=0, H=1)
def res(val, n):
    return val & ~(1 << n)
def set_(val, n):
    return val | (1 << n)

# execute opcode functions
def execOpc(opcode):
    global a, f, b, c, d, e, h, l, pc, sp, mem, disp
    
    # debug
    if DEBUG:
        print(f"PC: {pc}, OPCODE: {opcode}")

    # split into byte chunks
    o0 = (opcode & 0xf0) >> 4
    o1 = opcode & 0x0f

    # execute
    match o0:
        case 0:
            match o1:
                case 1: setbc(fetch16())
                case 2: mem[getbc()] = a
                case 3: setbc(add(getbc(), 1))
                case 4: b = add(b, 1)
                case 5: b = sub(b, 1)
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
                case 9: sethl(add(gethl(), getbc()))                    
                case 10: a = mem[getbc()]                    
                case 11: setbc(sub(getbc(), 1))                    
                case 12: c = add(c, 1)                  
                case 13: c = sub(c, 1)
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
                case 3: setde(add(getde(), 1))
                case 4: d = add(d, 1)
                case 5: d = sub(d, 1)
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
                case 9: sethl(add(gethl(), getde()))
                case 10: a = mem[getde()]
                case 11: setde(sub(getde(), 1))
                case 12: e = add(e, 1)
                case 13: e = sub(e, 1)
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
                case 3: sethl(add(gethl(), 1))
                case 4: h = add(h, 1)
                case 5: h = sub(h, 1)
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
                case 9: sethl(add(gethl(), gethl()))                 
                case 10: 
                    a = mem[gethl()]
                    sethl(gethl() + 1)
                case 11: sethl(sub(gethl(), 1))
                case 12: l = add(l, 1)
                case 13: l = sub(l, 1)
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
                case 3: sp = add(sp, 1)
                case 4: mem[gethl()] = add(mem[gethl()], 1)
                case 5: mem[gethl()] = sub(mem[gethl()], 1)
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
                case 9: sethl(add(gethl(), sp))
                case 10: 
                    a = mem[gethl()]
                    sethl(gethl() - 1)
                case 11: sp = sub(sp, 1)
                case 12: a = add(a, 1)
                case 13: a = sub(a, 1)
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
                case 0: a = add(a, b)
                case 1: a = add(a, c)
                case 2: a = add(a, d)
                case 3: a = add(a, e)
                case 4: a = add(a, h)
                case 5: a = add(a, l)
                case 6: a = add(a, mem[gethl()])
                case 7: a = add(a, a)
                case 8: a = adc(a, b)
                case 9: a = adc(a, c)
                case 10: a = adc(a, d)
                case 11: a = adc(a, e)
                case 12: a = adc(a, h)
                case 13: a = adc(a, l)
                case 14: a = adc(a, mem[gethl()])
                case 15: a = adc(a, a)
        case 9:
            match o1:
                case 0: a = sub(a, b)
                case 1: a = sub(a, c)
                case 2: a = sub(a, d)
                case 3: a = sub(a, e)
                case 4: a = sub(a, h)
                case 5: a = sub(a, l)
                case 6: a = sub(a, mem[gethl()])
                case 7: a = sub(a, a)
                case 8: a = sbc(a, b)
                case 9: a = sbc(a, c)
                case 10: a = sbc(a, d)
                case 11: a = sbc(a, e)
                case 12: a = sbc(a, h)
                case 13: a = sbc(a, l)
                case 14: a = sbc(a, mem[gethl()])
                case 15: a = sbc(a, a)
        case 10:
            match o1:
                case 0: a = and_(a, b)
                case 1: a = and_(a, c)
                case 2: a = and_(a, d)
                case 3: a = and_(a, e)
                case 4: a = and_(a, h)
                case 5: a = and_(a, l)
                case 6: a = and_(a, mem[gethl()])
                case 7: a = and_(a, a)
                case 8: a = xor(a, b)
                case 9: a = xor(a, c)
                case 10: a = xor(a, d)
                case 11: a = xor(a, e)
                case 12: a = xor(a, h)
                case 13: a = xor(a, l)
                case 14: a = xor(a, mem[gethl()])
                case 15: a = xor(a, a)
        case 11:
            match o1:
                case 0: a = or_(a, b)
                case 1: a = or_(a, c)
                case 2: a = or_(a, d)
                case 3: a = or_(a, e)
                case 4: a = or_(a, h)
                case 5: a = or_(a, l)
                case 6: a = or_(a, mem[gethl()])
                case 7: a = or_(a, a)
                case 8: a = cp(a, b)
                case 9: a = cp(a, c)
                case 10: a = cp(a, d)
                case 11: a = cp(a, e)
                case 12: a = cp(a, h)
                case 13: a = cp(a, l)
                case 14: a = cp(a, mem[gethl()])
                case 15: a = cp(a, a)
        case 12:
            match o1:
                case 0: 
                    if not isFlag(0x80):
                        pc = pop16()
                case 1: setbc(pop16())
                case 2:
                    if not isFlag(0x80):
                        pc = fetch16()
                case 3: pc = fetch16()
                case 4:
                    if not isFlag(0x80):
                        push16(pc)
                        pc = addr
                case 5: push16(getbc())
                case 6: a = add(a, fetch8())
                case 7:
                    push16(pc)
                    pc = 0
                case 8:
                    if isFlag(0x80):
                        pc = pop16()
                case 9: pc = pop16()
                case 10:
                    if isFlag(0x80):
                        pc = fetch16()
                case 11: pass # implement later
                case 12:
                    if isFlag(0x80):
                        push16(pc)
                        pc = fetch16()
                case 13:
                    push16(pc)
                    pc = fetch16()
                case 14: a = adc(a, fetch8())
                case 15:
                    push16(pc)
                    pc = 1
        case 13:
            match o1:
                case 0: 
                    if not isFlag(0x01):
                        pc = pop16()
                case 1: setde(pop16())
                case 2:
                    if not isFlag(0x01):
                        pc = fetch16()
                case 4:
                    if not isFlag(0x01):
                        push16(pc)
                        pc = addr
                case 5: push16(getde())
                case 6: a = sub(a, fetch8())
                case 7:
                    push16(pc)
                    pc = 2
                case 8:
                    if isFlag(0x01):
                        pc = pop16()
                case 9: pc = pop16()
                case 10:
                    if isFlag(0x01):
                        pc = fetch16()
                case 12:
                    if isFlag(0x01):
                        push16(pc)
                        pc = fetch16()
                case 13:
                    add(pc, 1)
                    execOpcCB(mem[pc])
                case 14: a = sbc(a, fetch8())
                case 15:
                    push16(pc)
                    pc = 3
        case 14:
            match o1:
                case 0: mem[fetch8()] = a
                case 1: sethl(pop16())
                case 2: mem[c] = a
                case 5: push16(gethl())
                case 6: a = and_(a, fetch8())
                case 7:
                    push16(pc)
                    pc = 4
                case 8: sp = add(sp, fetch8())
                case 9: pc = gethl()
                case 10: mem[fetch16()] = a
                case 14: a = xor(a, fetch8())
                case 15:
                    push16(pc)
                    pc = 5
        case 15:
            match o1:
                case 0: a = mem[fetch8()]
                case 1: setaf(pop16())
                case 2: a = mem[c]
                case 3: pass # implement later
                case 5: push16(getaf())
                case 6: a = or_(a, fetch8())
                case 7:
                    push16(pc)
                    pc = 6
                case 8:
                    sp = add(sp, fetch8())
                    sethl(sp)
                case 9: sp = gethl()
                case 10: a = fetch16()
                case 11: pass # implement later
                case 14: a = cp(a, fetch8())
                case 15:
                    push16(pc)
                    pc = 7
    
    # increment pc
    add(pc, 1)
def execOpcCB(opcode):
    global a, f, b, c, d, e, h, l, pc, sp, mem, disp
    
    # split into byte chunks
    o0 = (opcode & 0xf0) >> 4
    o1 = opcode & 0x0f
    
    # execute
    match o0:
        case 0:
            match o1:
                case 0: b = rlc(b)
                case 1: c = rlc(c)
                case 2: d = rlc(d)
                case 3: e = rlc(e)
                case 4: h = rlc(h)
                case 5: l = rlc(l)
                case 6: mem[gethl()] = rlc(mem[gethl()])
                case 7: a = rlc(a)
                case 8: b = rrc(b)
                case 9: c = rrc(c)
                case 10: d = rrc(d)
                case 11: e = rrc(e)
                case 12: h = rrc(h)
                case 13: l = rrc(l)
                case 14: mem[gethl()] = rrc(mem[gethl()])
                case 15: a = rrc(a)
        case 1:
            match o1:
                case 0: b = rl(b)
                case 1: c = rl(c)
                case 2: d = rl(d)
                case 3: e = rl(e)
                case 4: h = rl(h)
                case 5: l = rl(l)
                case 6: mem[gethl()] = rl(mem[gethl()])
                case 7: a = rl(a)
                case 8: b = rr(b)
                case 9: c = rr(c)
                case 10: d = rr(d)
                case 11: e = rr(e)
                case 12: h = rr(h)
                case 13: l = rr(l)
                case 14: mem[gethl()] = rr(mem[gethl()])
                case 15: a = rr(a)
        case 2:
            match o1:
                case 0: b = sla(b)
                case 1: c = sla(c)
                case 2: d = sla(d)
                case 3: e = sla(e)
                case 4: h = sla(h)
                case 5: l = sla(l)
                case 6: mem[gethl()] = sla(mem[gethl()])
                case 7: a = sla(a)
                case 8: b = sra(b)
                case 9: c = sra(c)
                case 10: d = sra(d)
                case 11: e = sra(e)
                case 12: h = sra(h)
                case 13: l = sra(l)
                case 14: mem[gethl()] = sra(mem[gethl()])
                case 15: a = sra(a)
        case 3:
            match o1:
                case 0: b = swap(b)
                case 1: c = swap(c)
                case 2: d = swap(d)
                case 3: e = swap(e)
                case 4: h = swap(h)
                case 5: l = swap(l)
                case 6: mem[gethl()] = swap(mem[gethl()])
                case 7: a = swap(a)
                case 8: b = srl(b)
                case 9: c = srl(c)
                case 10: d = srl(d)
                case 11: e = srl(e)
                case 12: h = srl(h)
                case 13: l = srl(l)
                case 14: mem[gethl()] = srl(mem[gethl()])
                case 15: a = srl(a)
        case 4:
            match o1:
                case 0: b = bit(0, b)
                case 1: c = bit(0, c)
                case 2: d = bit(0, d)
                case 3: e = bit(0, e)
                case 4: h = bit(0, l)
                case 5: l = bit(0, l)
                case 6: mem[gethl()] = bit(0, mem[gethl()])
                case 7: a = bit(0, a)
                case 8: b = bit(1, b)
                case 9: c = bit(1, c)
                case 10: d = bit(1, d)
                case 11: e = bit(1, e)
                case 12: h = bit(1, h)
                case 13: l = bit(1, l)
                case 14: mem[gethl()] = bit(1, mem[gethl()])
                case 15: a = bit(1, a)
        case 5:
            match o1:
                case 0: b = bit(2, b)
                case 1: c = bit(2, c)
                case 2: d = bit(2, d)
                case 3: e = bit(2, e)
                case 4: h = bit(2, l)
                case 5: l = bit(2, l)
                case 6: mem[gethl()] = bit(2, mem[gethl()])
                case 7: a = bit(2, a)
                case 8: b = bit(3, b)
                case 9: c = bit(3, c)
                case 10: d = bit(3, d)
                case 11: e = bit(3, e)
                case 12: h = bit(3, h)
                case 13: l = bit(3, l)
                case 14: mem[gethl()] = bit(3, mem[gethl()])
                case 15: a = bit(3, a)
        case 6:
            match o1:
                case 0: b = bit(4, b)
                case 1: c = bit(4, c)
                case 2: d = bit(4, d)
                case 3: e = bit(4, e)
                case 4: h = bit(4, l)
                case 5: l = bit(4, l)
                case 6: mem[gethl()] = bit(4, mem[gethl()])
                case 7: a = bit(4, a)
                case 8: b = bit(5, b)
                case 9: c = bit(5, c)
                case 10: d = bit(5, d)
                case 11: e = bit(5, e)
                case 12: h = bit(5, h)
                case 13: l = bit(5, l)
                case 14: mem[gethl()] = bit(5, mem[gethl()])
                case 15: a = bit(5, a)
        case 7:
            match o1:
                case 0: b = bit(6, b)
                case 1: c = bit(6, c)
                case 2: d = bit(6, d)
                case 3: e = bit(6, e)
                case 4: h = bit(6, l)
                case 5: l = bit(6, l)
                case 6: mem[gethl()] = bit(6, mem[gethl()])
                case 7: a = bit(6, a)
                case 8: b = bit(7, b)
                case 9: c = bit(7, c)
                case 10: d = bit(7, d)
                case 11: e = bit(7, e)
                case 12: h = bit(7, h)
                case 13: l = bit(7, l)
                case 14: mem[gethl()] = bit(7, mem[gethl()])
                case 15: a = bit(7, a)
        case 8:
            match o1:
                case 0: b = res(0, b)
                case 1: c = res(0, c)
                case 2: d = res(0, d)
                case 3: e = res(0, e)
                case 4: h = res(0, l)
                case 5: l = res(0, l)
                case 6: mem[gethl()] = res(0, mem[gethl()])
                case 7: a = res(0, a)
                case 8: b = res(1, b)
                case 9: c = res(1, c)
                case 10: d = res(1, d)
                case 11: e = res(1, e)
                case 12: h = res(1, h)
                case 13: l = res(1, l)
                case 14: mem[gethl()] = res(1, mem[gethl()])
                case 15: a = res(1, a)
        case 9:
            match o1:
                case 0: b = res(2, b)
                case 1: c = res(2, c)
                case 2: d = res(2, d)
                case 3: e = res(2, e)
                case 4: h = res(2, l)
                case 5: l = res(2, l)
                case 6: mem[gethl()] = res(2, mem[gethl()])
                case 7: a = res(2, a)
                case 8: b = res(3, b)
                case 9: c = res(3, c)
                case 10: d = res(3, d)
                case 11: e = res(3, e)
                case 12: h = res(3, h)
                case 13: l = res(3, l)
                case 14: mem[gethl()] = res(3, mem[gethl()])
                case 15: a = res(3, a)
        case 10:
            match o1:
                case 0: b = res(4, b)
                case 1: c = res(4, c)
                case 2: d = res(4, d)
                case 3: e = res(4, e)
                case 4: h = res(4, l)
                case 5: l = res(4, l)
                case 6: mem[gethl()] = res(4, mem[gethl()])
                case 7: a = res(4, a)
                case 8: b = res(5, b)
                case 9: c = res(5, c)
                case 10: d = res(5, d)
                case 11: e = res(5, e)
                case 12: h = res(5, h)
                case 13: l = res(5, l)
                case 14: mem[gethl()] = res(5, mem[gethl()])
                case 15: a = res(5, a)
        case 11:
            match o1:
                case 0: b = res(0, b)
                case 1: c = res(0, c)
                case 2: d = res(0, d)
                case 3: e = res(0, e)
                case 4: h = res(0, l)
                case 5: l = res(0, l)
                case 6: mem[gethl()] = res(0, mem[gethl()])
                case 7: a = res(0, a)
                case 8: b = res(1, b)
                case 9: c = res(1, c)
                case 10: d = res(1, d)
                case 11: e = res(1, e)
                case 12: h = res(1, h)
                case 13: l = res(1, l)
                case 14: mem[gethl()] = res(1, mem[gethl()])
                case 15: a = res(1, a)
        case 12:
            match o1:
                case 0: b = set_(0, b)
                case 1: c = set_(0, c)
                case 2: d = set_(0, d)
                case 3: e = set_(0, e)
                case 4: h = set_(0, l)
                case 5: l = set_(0, l)
                case 6: mem[gethl()] = set_(0, mem[gethl()])
                case 7: a = set_(0, a)
                case 8: b = set_(1, b)
                case 9: c = set_(1, c)
                case 10: d = set_(1, d)
                case 11: e = set_(1, e)
                case 12: h = set_(1, h)
                case 13: l = set_(1, l)
                case 14: mem[gethl()] = set_(1, mem[gethl()])
                case 15: a = set_(1, a)
        case 13:
            match o1:
                case 0: b = set_(2, b)
                case 1: c = set_(2, c)
                case 2: d = set_(2, d)
                case 3: e = set_(2, e)
                case 4: h = set_(2, l)
                case 5: l = set_(2, l)
                case 6: mem[gethl()] = set_(2, mem[gethl()])
                case 7: a = set_(2, a)
                case 8: b = set_(3, b)
                case 9: c = set_(3, c)
                case 10: d = set_(3, d)
                case 11: e = set_(3, e)
                case 12: h = set_(3, h)
                case 13: l = set_(3, l)
                case 14: mem[gethl()] = set_(3, mem[gethl()])
                case 15: a = set_(3, a)
        case 14:
            match o1:
                case 0: b = set_(4, b)
                case 1: c = set_(4, c)
                case 2: d = set_(4, d)
                case 3: e = set_(4, e)
                case 4: h = set_(4, l)
                case 5: l = set_(4, l)
                case 6: mem[gethl()] = set_(4, mem[gethl()])
                case 7: a = set_(4, a)
                case 8: b = set_(5, b)
                case 9: c = set_(5, c)
                case 10: d = set_(5, d)
                case 11: e = set_(5, e)
                case 12: h = set_(5, h)
                case 13: l = set_(5, l)
                case 14: mem[gethl()] = set_(5, mem[gethl()])
                case 15: a = set_(5, a)
        case 15:
            match o1:
                case 0: b = set_(6, b)
                case 1: c = set_(6, c)
                case 2: d = set_(6, d)
                case 3: e = set_(6, e)
                case 4: h = set_(6, l)
                case 5: l = set_(6, l)
                case 6: mem[gethl()] = set_(6, mem[gethl()])
                case 7: a = set_(6, a)
                case 8: b = set_(7, b)
                case 9: c = set_(7, c)
                case 10: d = set_(7, d)
                case 11: e = set_(7, e)
                case 12: h = set_(7, h)
                case 13: l = set_(7, l)
                case 14: mem[gethl()] = set_(7, mem[gethl()])
                case 15: a = set_(7, a)

    # increment pc
    add(pc, 1)

# screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Boy Emulator")

# load rom
loadRom("pokemon-red.gb")

# main run loop
run = True
while run:
    # events
    for event in pygame.event.get():
        # quit event
        if event.type == pygame.QUIT:
            run = False
            
    # run instructions
    for _ in range(MC // 60):
        execOpc(mem[pc])

    # refresh rate
    updScreen()
    pclock.tick(60)

# quit
pygame.quit()
