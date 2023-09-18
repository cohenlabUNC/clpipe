import pytest
from pathlib import Path

from clpipe.bids import get_bids

def test_get_bids(clpipe_bids_dir: Path):
    get_bids(clpipe_bids_dir)
    