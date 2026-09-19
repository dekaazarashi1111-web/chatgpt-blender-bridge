"""Closed, thin cheek cover following the exact continuous head surface."""
import numpy as np
from math import sin,cos,pi

def outline(points,sub=8):
    out=[]
    for i in range(len(points)):
        a,b,c,d=[points[j%len(points)] for j in [i-1,i,i+1,i+2]]
        for k in range(sub):
            t=k/sub
            out.append(tuple(.5*((2*b[j])+(-a[j]+c[j])*t+(2*a[j]-5*b[j]+4*c[j]-d[j])*t*t+(-a[j]+3*b[j]-3*c[j]+d[j])*t*t*t) for j in range(2)))
    return out

def cheek_mesh(sign,front_surface,cutter=False):
    edge=outline([(.227,1.752),(.195,1.742),(.165,1.723),(.147,1.697),(.147,1.666),(.152,1.646),(.175,1.638),(.205,1.659),(.229,1.686),(.238,1.714),(.237,1.741)])
    nr=44;n=len(edge);xz=[];lats=[]
    factor=1.080 if cutter else 1.0
    for i in range(nr):
        lat=-pi/2+pi*(i+.15)/(nr-.7)
        for xx,zz in edge:
            x=.190+(xx-.190)*cos(lat)*factor;z=1.696+(zz-1.696)*cos(lat)*factor
            xz.append((sign*x,z));lats.append(lat)
    xz=np.asarray(xz);ys=front_surface(xz[:,0],xz[:,1]);verts=[]
    for (x,z),y,lat in zip(xz,ys,lats):
        offset=(-.010 if lat<0 else .024)*abs(sin(lat)) if cutter else (-.004 if lat<0 else .015)*abs(sin(lat))
        verts.append((float(x),float(y-.001+offset),float(z)))
    faces=[]
    for i in range(nr-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend([tuple(reversed(range(n))),tuple((nr-1)*n+j for j in range(n))])
    return verts,faces
