import pytest

from nids import config
from nids.data import load_split

needs_data = pytest.mark.skipif(
    not (config.TRAIN_CSV.exists() and config.TEST_CSV.exists()),
    reason="UNSW-NB15 CSVs not downloaded into data/raw/",
)


def test_rejects_unknown_split():
    with pytest.raises(ValueError):
        load_split("validation")


@needs_data
@pytest.mark.parametrize("split", ["train", "test"])
def test_official_row_counts(split):
    assert len(load_split(split)) == config.EXPECTED_ROWS[split]


@needs_data
def test_train_and_test_share_schema():
    assert list(load_split("train").columns) == list(load_split("test").columns)
