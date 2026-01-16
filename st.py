import streamlit as st
import os, sys

# PyTorch 2.6+ compatibility fix
import torch
try:
    from omegaconf.listconfig import ListConfig
    from omegaconf.dictconfig import DictConfig
    from omegaconf.base import ContainerMetadata, Metadata
    torch.serialization.add_safe_globals([ListConfig, DictConfig, ContainerMetadata, Metadata])
except Exception:
    pass

# Monkey patch to force weights_only=False
original_load = torch.load
def patched_load(*args, **kwargs):
    if 'weights_only' in kwargs:
        kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = patched_load

from core.st_utils.imports_and_utils import *
from core import *

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
