import os
import sys

# Add the current directory to the module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from CStructParser import CStructParser
from ctype_format import CTypeFormat

__version__ = '0.1.0'
__all__ = ['CStructParser', 'CTypeFormat']