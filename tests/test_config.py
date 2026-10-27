from nids import config


def test_project_root_is_repo_root():
    assert (config.PROJECT_ROOT / "requirements.txt").exists()


def test_data_paths_live_under_raw_dir():
    assert config.TRAIN_CSV.parent == config.RAW_DIR
    assert config.TEST_CSV.parent == config.RAW_DIR
