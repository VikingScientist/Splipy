from itertools import islice

import numpy as np

from pxr import Usd, UsdGeom
from ..curve import Curve
from ..surface import Surface
from ..volume import Volume
from ..splineobject import SplineObject
from ..basis import BSplineBasis

from .master import MasterIO


class USD(MasterIO):

    def __init__(self, filename, binary=True):
        # technically you can represent both ascii and binary files with .usd,
        # but we here enforce clarity in file extension
        if filename.endswith('.usd'):
            if binary: filename += 'c' # binary files are denoted '.usdc'
            else:      filename += 'a' # ascii files are denoted '.usda'
        if binary and not filename.endswith('.usdc'):
            filename += '.usdc'
        if not binary and not filename.endswith('.usda'):
            filename += '.usda'
        self.filename = filename
        self.binary = binary
        self.patch_count = 0

    def __enter__(self):
        self.stage = Usd.Stage.CreateNew(self.filename)
        return self

    def read(self):
        raise IOError('Reading from USD files not supported')

    def write_surface(self, surf, edge=None):
        if edge is None:
            patch = UsdGeom.NurbsPatch.Define(self.stage, f'/patch{self.patch_count}/spline')
        else:
            patch = UsdGeom.NurbsPatch.Define(self.stage, f'/patch{self.patch_count}/edge{edge}')
        patch.CreateUOrderAttr().Set(surf.order('u'))
        patch.CreateVOrderAttr().Set(surf.order('v'))

        patch.CreateUVertexCountAttr().Set(surf.shape[0])
        patch.CreateVVertexCountAttr().Set(surf.shape[1])

        patch.CreateUKnotsAttr().Set(surf.knots('u', True))
        patch.CreateVKnotsAttr().Set(surf.knots('v', True))

        
        if surf.rational:
            cp      = surf[:,:,:-1]
            weights = surf[:,:, -1]
            for d in range(surf.dimension):
                cp[:,:,d] /= weights
            patch.CreatePointsAttr().Set(      np.swapaxes(cp,     0,1))
            patch.CreatePointWeightsAttr().Set(np.swapaxes(weights,0,1))
        else:
            patch.CreatePointsAttr().Set(surf[:])

    def write(self, obj):
        # In case of list-like input (i.e. splinemodel object), write all objects separately
        if isinstance(obj[0], SplineObject):
            for o in obj:
                self.write(o)
            return
        
        # break periodicity 
        for i in range(obj.pardim):
            if obj.periodic(i):
                obj = obj.split(obj.start(i), i)
        print(obj)

        if isinstance(obj, Volume):
            # in case of volume, write all 6 boundary edges
            self.xformPrim = UsdGeom.Xform.Define(self.stage, f'/patch{self.patch_count}')
            for i,surf in enumerate(obj.faces()):
                # reorient normal so it is pointing outward
                if i in [0,3,4]:
                    surf.swap()
                self.write_surface(surf, i)
            self.patch_count += 1

        elif isinstance(obj, Surface):
            self.write_surface(obj)
            self.patch_count += 1
            

    def __exit__(self, exc_type, exc_value, traceback):
        self.stage.GetRootLayer().Save()
