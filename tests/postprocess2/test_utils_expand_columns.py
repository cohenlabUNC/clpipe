import pytest
import os

from clpipe.postprocutils.utils import *
from typing import List

@pytest.fixture(scope = "function")
def sample_confound_columns() -> List[str]:
    return ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1"]


def test_expand_columns_no_expansion(sample_confounds_timeseries, sample_confound_columns):
    expanded_columns: List[str] = expand_columns(sample_confounds_timeseries, sample_confound_columns)
    expected_columns: List[str] = sample_confound_columns
    assert len(expanded_columns) == len(expected_columns)
    assert sorted(expanded_columns) == sorted(expected_columns)


def test_expand_columns_pattern_at_end(sample_confounds_timeseries, sample_confound_columns):
    sample_confound_columns.append("t_comp_cor*")
    expanded_columns: List[str] = expand_columns(sample_confounds_timeseries, sample_confound_columns)
    expected_columns: List[str] = ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1",
    "t_comp_cor_00", "t_comp_cor_01", "t_comp_cor_02", "t_comp_cor_03"]
    assert len(expanded_columns) == len(expected_columns)
    assert sorted(expanded_columns) == sorted(expected_columns)


def test_expand_columns_pattern_at_start(sample_confounds_timeseries, sample_confound_columns):
    sample_confound_columns.extend(["*vars", "t_comp_cor*"])
    expanded_columns: List[str] = expand_columns(sample_confounds_timeseries, sample_confound_columns)
    expected_columns: List[str] = ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1",
    "std_dvars", "dvars", "t_comp_cor_00", "t_comp_cor_01", "t_comp_cor_02", "t_comp_cor_03"]
    assert len(expanded_columns) == len(expected_columns)
    assert sorted(expanded_columns) == sorted(expected_columns)