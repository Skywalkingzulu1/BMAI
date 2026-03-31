import sys
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
import release


def test_run_tests_calls_pytest(monkeypatch):
    """run_tests should invoke pytest via subprocess.run."""
    mock_run = mock.Mock()
    mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(release.subprocess, "run", mock_run)

    # Execute the function
    release.run_tests()

    # Verify that subprocess.run was called with the expected command
    expected_cmd = [sys.executable, "-m", "pytest", "-q"]
    mock_run.assert_called_once_with(
        expected_cmd,
        cwd=None,
        text=True,
        capture_output=False,
        check=False,
    )


def test_build_docker_image_constructs_correct_command(monkeypatch):
    """build_docker_image should call docker build with proper arguments."""
    mock_run = mock.Mock()
    mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(release.subprocess, "run", mock_run)

    version = "v1.2.3"
    registry = "ghcr.io/user/bmai"
    dockerfile = "Dockerfile.dev"

    release.build_docker_image(version, registry, dockerfile)

    image_tag = f"{registry}:{version}"
    expected_cmd = [
        "docker",
        "build",
        "-t",
        image_tag,
        "-f",
        dockerfile,
        ".",
    ]
    mock_run.assert_called_once_with(
        expected_cmd,
        cwd=None,
        text=True,
        capture_output=False,
        check=False,
    )


def test_push_docker_image_calls_docker_push(monkeypatch):
    """push_docker_image should invoke docker push with the correct tag."""
    mock_run = mock.Mock()
    mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(release.subprocess, "run", mock_run)

    version = "v2.0.0"
    registry = "docker.io/library/bmai"

    release.push_docker_image(version, registry)

    image_tag = f"{registry}:{version}"
    expected_cmd = ["docker", "push", image_tag]
    mock_run.assert_called_once_with(
        expected_cmd,
        cwd=None,
        text=True,
        capture_output=False,
        check=False,
    )


def test_create_git_tag_runs_git_commands(monkeypatch):
    """create_git_tag should run git tag and git push commands."""
    mock_run = mock.Mock()
    mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(release.subprocess, "run", mock_run)

    version = "v3.1.4"
    release.create_git_tag(version)

    # Expect two calls: git tag and git push
    expected_calls = [
        mock.call(
            ["git", "tag", version],
            cwd=None,
            text=True,
            capture_output=False,
            check=False,
        ),
        mock.call(
            ["git", "push", "origin", version],
            cwd=None,
            text=True,
            capture_output=False,
            check=False,
        ),
    ]
    assert mock_run.call_args_list == expected_calls


def test_main_flow_with_registry(monkeypatch):
    """Full main flow when a registry is provided should run tests, build, push, and tag."""
    # Mock all external command calls
    mock_run = mock.Mock()
    mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(release.subprocess, "run", mock_run)

    # Mock sys.argv for argparse
    test_version = "v0.0.1"
    test_registry = "example.com/repo/bmai"
    test_dockerfile = "Dockerfile.test"
    monkeypatch.setattr(sys, "argv", ["release.py", test_version, "--registry", test_registry, "--dockerfile", test_dockerfile])

    # Run main
    release.main()

    # Build expected command list in order
    expected_commands = [
        # run_tests
        [sys.executable, "-m", "pytest", "-q"],
        # build_docker_image
        [
            "docker",
            "build",
            "-t",
            f"{test_registry}:{test_version}",
            "-f",
            test_dockerfile,
            ".",
        ],
        # push_docker_image
        ["docker", "push", f"{test_registry}:{test_version}"],
        # create_git_tag (git tag)
        ["git", "tag", test_version],
        # create_git_tag (git push)
        ["git", "push", "origin", test_version],
    ]

    # Verify that subprocess.run was called with each expected command in order
    actual_calls = [call.args[0] for call in mock_run.call_args_list]
    assert actual_calls == expected_commands
```