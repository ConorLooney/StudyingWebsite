import random

def gen_random_code(length=16):
    random.seed()
    digits = "1,2,3,4,5,6,7,8,9,0,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,u,s,t,v,w,x,y,z,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,U,S,T,V,W,X,Y,Z".split(",")
    code = ""
    for n in range(length):
        code += digits[random.randint(0, len(digits)-1)]
    return code

def remove_duplicate_rows(rows, identifying_field_name):
    """Return new list of rows where no row in the list has the same value
    for the given identifying field name as any other row in the list
    
    :type rows: list of sqlite row objects 
    """
    unique_rows_dict = {}
    for row in rows:
        unique_rows_dict[row[identifying_field_name]] = row
    unique_rows_list = list(unique_rows_dict.values())
    return unique_rows_list