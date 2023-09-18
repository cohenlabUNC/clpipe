import pytest
from pathlib import Path

from clpipe.bids import get_bids

def test_get_bids(clpipe_bids_dir: Path):
    layout = get_bids(clpipe_bids_dir / "data_BIDS")
    
    # Practice stuff querying for layout...
    # Test for values returned from the queries.

    