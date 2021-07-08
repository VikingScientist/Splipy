from .g2  import G2
from .svg import SVG
from .spl import SPL
from .stl import STL
from .ofoam import OpenFOAM


# GRDECL depends on optional cv2
try:
    from .grdecl import GRDECL
    has_grdecl = True
except ImportError:
    has_grdecl = False


# ThreeDM depends on optional rhino3dm
try:
    from .threedm import ThreeDM
    has_rhino = True
except ImportError:
    has_rhino = False


# USD depends on optional pxr
try:
    from pxr import Usd
    from .usd import USD
    has_usd = True
except ImportError:
    has_usd = False



__all__ = ['G2', 'SVG', 'SPL', 'STL', 'OpenFOAM']

if has_grdecl:
    __all__.append('GRDECL')

if has_rhino:
    __all__.append('ThreeDM')

if has_usd:
    __all__.append('USD')
