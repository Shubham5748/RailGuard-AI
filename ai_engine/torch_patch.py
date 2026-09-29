"""
torch_patch.py  –  Must be imported BEFORE any ultralytics import.
Patches torch.load to use weights_only=False on PyTorch >= 2.0
so that Ultralytics YOLO models load correctly.
"""
import torch as _torch

_orig_load = _torch.load

def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_load(*args, **kwargs)

_torch.load = _patched_load
