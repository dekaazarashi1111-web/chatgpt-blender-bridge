"""Project-local NumPy implicit-surface mesher. No external models or image synthesis.
Six tetrahedra share a consistent cube diagonal; grid-edge identities weld vertices.
"""
import numpy as np


def smooth_union(a, b, radius):
    h = np.maximum(radius - np.abs(a-b), 0.0) / radius
    return np.minimum(a,b) - h*h*radius*.25


def ellipsoid(x, y, z, center, radii):
    q0=(x-center[0])/radii[0];q1=(y-center[1])/radii[1];q2=(z-center[2])/radii[2]
    k0=np.sqrt(q0*q0+q1*q1+q2*q2)
    k1=np.sqrt((q0/radii[0])**2+(q1/radii[1])**2+(q2/radii[2])**2)
    return np.where(k0<1e-6,-min(radii),k0*(k0-1)/np.maximum(k1,1e-8))


def rounded_box(x,y,z,center,half,radius):
    qx=np.abs(x-center[0])-(half[0]-radius)
    qy=np.abs(y-center[1])-(half[1]-radius)
    qz=np.abs(z-center[2])-(half[2]-radius)
    outside=np.sqrt(np.maximum(qx,0)**2+np.maximum(qy,0)**2+np.maximum(qz,0)**2)
    return outside+np.minimum(np.maximum(np.maximum(qx,qy),qz),0)-radius


def head_field(x,y,z):
    # Smooth crown; no stacked loft profiles or curvature-discontinuous row joins.
    cranium=ellipsoid(x,y,z,(0,-.036,1.797),(.206,.201,.208))
    bridge=ellipsoid(x,y,z,(0,-.221,1.746),(.054,.052,.116))
    field=smooth_union(cranium,bridge,.035)
    for sign in (-1,1):
        cushion=rounded_box(x,y,z,(sign*.058,-.268,1.662),(.068,.067,.053),.032)
        field=smooth_union(field,cushion,.024)
    # A tiny parting cleft, not a groove cut through the entire nasal bridge.
    cleft=ellipsoid(x,y,z,(0,-.339,1.618),(.0065,.016,.039))
    field=np.maximum(field,-cleft)
    mouth=ellipsoid(x,y,z,(0,-.236,1.531),(.151,.171,.078))
    field=np.maximum(field,-mouth)
    for sign in (-1,1):
        orbit=ellipsoid(x,y,z,(sign*.069,-.231,1.823),(.044,.081,.053))
        field=np.maximum(field,-orbit)
    return field


def isosurface(field_function, lower, upper, spacing=.0020):
    axes=[np.linspace(lower[i],upper[i],int(np.ceil((upper[i]-lower[i])/spacing))+1,dtype=np.float32) for i in range(3)]
    nx,ny,nz=[len(a) for a in axes]
    values=np.asarray(field_function(axes[0][:,None,None],axes[1][None,:,None],axes[2][None,None,:]),dtype=np.float32)
    if not np.isfinite(values).all():raise ValueError('Non-finite implicit field')
    if any(np.min(face)<=0 for face in (values[0],values[-1],values[:,0],values[:,-1],values[:,:,0],values[:,:,-1])):
        raise ValueError('Isosurface touches its sampling-domain boundary')
    offsets=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)],dtype=np.int64)
    cuts=[values[a:nx-1+a,b:ny-1+b,c:nz-1+c] for a,b,c in offsets]
    low=cuts[0].copy();high=cuts[0].copy()
    for v in cuts[1:]:np.minimum(low,v,out=low);np.maximum(high,v,out=high)
    active=np.column_stack(np.nonzero((low<0)&(high>0)));del low,high,cuts
    origin=(active[:,0]*ny+active[:,1])*nz+active[:,2]
    delta=(offsets[:,0]*ny+offsets[:,1])*nz+offsets[:,2]
    ids=origin[:,None]+delta[None,:];flat=values.ravel();samples=flat[ids]
    tetra=[(0,5,1,6),(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6)]
    edges=[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
    patterns={1:[(0,2,3)],2:[(0,1,4)],4:[(1,2,5)],8:[(3,4,5)],3:[(2,1,4),(2,4,3)],5:[(0,1,5),(0,5,3)],6:[(0,2,5),(0,5,4)]}
    for case,triangles in list(patterns.items()):patterns[15-case]=[tuple(reversed(t)) for t in triangles]
    batches=[]
    for tet in tetra:
        code=sum((samples[:,tet[k]]<0).astype(np.uint8)*(1<<k) for k in range(4))
        for case,triangles in patterns.items():
            selected=ids[code==case][:,tet]
            if not len(selected):continue
            for triangle in triangles:
                endpoints=np.stack([selected[:,edges[e]] for e in triangle],axis=1)
                batches.append(np.sort(endpoints,axis=2))
    pairs=np.concatenate(batches,axis=0).reshape(-1,2);del batches,samples,ids
    unique,inverse=np.unique(pairs,axis=0,return_inverse=True);del pairs
    def coordinates(indices):
        i=indices//(ny*nz);j=(indices//nz)%ny;k=indices%nz
        return np.column_stack((axes[0][i],axes[1][j],axes[2][k])).astype(np.float64)
    a=coordinates(unique[:,0]);b=coordinates(unique[:,1]);fa=flat[unique[:,0]].astype(np.float64);fb=flat[unique[:,1]].astype(np.float64)
    fraction=fa/(fa-fb);verts=a+(b-a)*fraction[:,None];faces=inverse.reshape(-1,3)
    if not np.isfinite(verts).all():raise ValueError('Non-finite mesh')
    return verts.tolist(),faces.tolist(),{'grid_shape':[nx,ny,nz],'active_cells':int(len(active)),'spacing_requested':spacing,'vertices':len(verts),'triangles':len(faces),'method':'six-tetrahedra / exact shared-grid-edge welding'}
