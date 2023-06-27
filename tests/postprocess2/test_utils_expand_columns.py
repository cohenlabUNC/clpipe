import pytest
import os

from clpipe.postprocutils.utils import *

@pytest.fixture(scope = "function")
def sample_confound_columns() -> List[str]:
    return ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1"]

@pytest.fixture(scope = "function")
def sample_confound_timeseries() -> List[str]:
    return ["global_signal", "global_signal_derivative1", "global_signal_power2",
    "global_signal_derivative1_power2", "csf", "csf_derivative1", "csf_power2",
    "csf_derivative1_power2", "white_matter", "white_matter_derivative1",
    "white_matter_power2", "white_matter_derivative1_power2", "csf_wm", "tcompcor",
    "std_dvars", "dvars", "framewise_displacement",	"rmsd",	"t_comp_cor_00", 
    "t_comp_cor_01", "t_comp_cor_02", "t_comp_cor_03", "a_comp_cor_00",	
    "a_comp_cor_01", "a_comp_cor_02", "a_comp_cor_03", "a_comp_cor_04", 
    "a_comp_cor_05", "a_comp_cor_06", "a_comp_cor_07", "a_comp_cor_08",	
    "a_comp_cor_09", "a_comp_cor_10", "cosine00	cosine01", "cosine02", "cosine03",	
    "cosine04", "cosine05",	"cosine06",	"cosine07",	"cosine08",	"cosine09",	
    "cosine10",	"non_steady_state_outlier00", "trans_x", "trans_x_derivative1",	
    "trans_x_power2", "trans_x_derivative1_power2",	"trans_y", "trans_y_derivative1",
    "trans_y_power2", "trans_y_derivative1_power2", "trans_z", "trans_z_derivative1",
    "trans_z_power2", "trans_z_derivative1_power2",	"rot_x", "rot_x_derivative1", 
    "rot_x_power2",	"rot_x_derivative1_power2",	"rot_y", "rot_y_derivative1", 
    "rot_y_power2",	"rot_y_derivative1_power2",	"rot_z", "rot_z_derivative1",
    "rot_z_derivative1_power2",	"rot_z_power2",	"motion_outlier00",	
    "motion_outlier01",	"motion_outlier02"]


def test_expand_columns_no_expansion(sample_confound_timeseries, sample_confound_columns):
    expanded_columns: List[str] = expand_columns(sample_confound_timeseries, sample_confound_columns)
    expected_columns: List[str] = sample_confound_columns
    assert len(expanded_columns) == len(expected_columns)
    assert sorted(expanded_columns) == sorted(expected_columns)


def test_expand_columns_pattern_at_end(sample_confound_timeseries, sample_confound_columns):
    sample_confound_columns.append("t_comp_cor*")
    expanded_columns: List[str] = expand_columns(sample_confound_timeseries, sample_confound_columns)
    expected_columns: List[str] = ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1",
    "t_comp_cor_00", "t_comp_cor_01", "t_comp_cor_02", "t_comp_cor_03"]
    assert len(expanded_columns) == len(expected_columns)
    assert sorted(expanded_columns) == sorted(expected_columns)


def test_expand_columns_pattern_at_start(sample_confounds_timeseries, sample_confound_columns):
    sample_confound_columns.extend(["*vars", "t_comp_cor*"])
    expanded_columns: List[str] = expand_columns(sample_confound_timeseries, sample_confound_columns)
    expected_columns: List[str] = ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1",
    "std_vars", "dvars", "t_comp_cor_00", "t_comp_cor_01", "t_comp_cor_02", "t_comp_cor_03"]
    assert len(expanded_columns) == len(expected_columns)
    assert sorted(expanded_columns) == sorted(expected_columns)