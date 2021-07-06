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

    def __init__(self, filename):
        # the filename extension encodes to store ascii (.usda) or binary (.usdc)
        if filename.endswith('.usdc'):
            self.binary = True
        elif filename.endswith('.usda'):
            self.binary = False
        elif filename.endswith('.usd'): # .usd-files can contain EITHER ascii or binary. Default is binary though
            self.binary = True
        else:
            filename += '.usd'
            self.binary = True

        self.filename = filename
        self.patch_count = 0
        self.curve_count = 0

    def __enter__(self):
        self.stage = Usd.Stage.CreateNew(self.filename)
        return self

    def read(self):
        raise IOError('Reading from USD files not supported')

    def write_curve(self, crv):
        patch = UsdGeom.NurbsCurves.Define(self.stage, f'/curve{self.curve_count}/spline')

        patch.CreateOrderAttr().Set([crv.order('u')])
        patch.CreateCurveVertexCountsAttr().Set([crv.shape[0]  ])
        patch.CreateKnotsAttr().Set(crv.knots('u', True))
        patch.CreateWidthsAttr().Set([.2])

        if crv.rational:
            raise RuntimeError('Rational curves are unsupported in USD format. Consider calling rebuild() on curve to force a nonrational representation')
            cp      = crv[:,:-1]
            weights = crv[:, -1]
            for d in range(crv.dimension):
                cp[:,d] /= weights
            patch.CreatePointsAttr().Set(cp)
            patch.CreatePointWeightsAttr().Set(weights)
        else:
            patch.CreatePointsAttr().Set(crv[:])


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

        # enforce 3D
        obj = obj.set_dimension(3)

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

        elif isinstance(obj, Curve):
            self.write_curve(obj)
            self.curve_count += 1


    def __exit__(self, exc_type, exc_value, traceback):
        self.stage.GetRootLayer().Save()
