import math

# MediaPipe indices
HEAD = 0
LS, RS = 11, 12
LE, RE = 13, 14
LW, RW = 15, 16
LH, RH = 23, 24
LK, RK = 25, 26
LA, RA = 27, 28

def visible(lm):
    return lm.visibility > 0.6

def px_dist(a, b, w, h):
    return math.sqrt(((a.x - b.x)*w)**2 + ((a.y - b.y)*h)**2)

def confidence(lm):
    return sum(1 for p in lm if p.visibility > 0.6) / len(lm)

def body_type(lm):
    if visible(lm[LA]) and visible(lm[LH]):
        return "full"
    if visible(lm[LS]) and visible(lm[LH]):
        return "upper"
    return "reject"
