import pytest

from scripts.release import project_version, verify_tag


def test_release_tag_must_match_project_version():
    verify_tag(f"v{project_version()}")
    with pytest.raises(SystemExit):
        verify_tag("v0.0.0-wrong")
