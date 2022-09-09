import random

def gen_random_code(length=16):
    random.seed()
    digits = "1,2,3,4,5,6,7,8,9,0,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,u,s,t,v,w,x,y,z".split(",")
    code = ""
    for n in range(length):
        code += digits[random.randint(0, len(digits)-1)]
    return code