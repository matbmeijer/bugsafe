"""Tests for bundle schema models."""

from datetime import datetime

from bugsafe.bundle.schema import (
    BUNDLE_VERSION,
    BugBundle,
    BundleMetadata,
    CaptureOutput,
    Environment,
    Frame,
    GitInfo,
    PackageInfo,
    Traceback,
)


class TestFrame:
    """Test Frame model."""

    def test_frame_creation(self) -> None:
        """Test creating a frame."""
        frame = Frame(file="/path/to/file.py", line=42, function="test_func")
        assert frame.file == "/path/to/file.py"
        assert frame.line == 42
        assert frame.function == "test_func"

    def test_frame_with_code(self) -> None:
        """Test frame with code snippet."""
        frame = Frame(
            file="test.py",
            line=10,
            function="main",
            code="    print('hello')",
        )
        assert frame.code == "    print('hello')"

    def test_frame_with_locals(self) -> None:
        """Test frame with local variables."""
        frame = Frame(
            file="test.py",
            line=5,
            function="func",
            locals={"x": "1", "y": "'hello'"},
        )
        assert frame.locals == {"x": "1", "y": "'hello'"}

    def test_frame_minimal(self) -> None:
        """Test frame with minimal required fields."""
        frame = Frame(file="f.py", line=1)
        assert frame.file == "f.py"
        assert frame.line == 1
        assert frame.function is None
        assert frame.code is None
        assert frame.locals is None


class TestTraceback:
    """Test Traceback model."""

    def test_traceback_creation(self) -> None:
        """Test creating a traceback."""
        tb = Traceback(exception_type="ValueError", message="invalid value")
        assert tb.exception_type == "ValueError"
        assert tb.message == "invalid value"
        assert tb.frames == []

    def test_traceback_with_frames(self) -> None:
        """Test traceback with frames."""
        frames = [
            Frame(file="a.py", line=1, function="func_a"),
            Frame(file="b.py", line=2, function="func_b"),
        ]
        tb = Traceback(
            exception_type="RuntimeError",
            message="oops",
            frames=frames,
        )
        assert len(tb.frames) == 2
        assert tb.frames[0].function == "func_a"

    def test_traceback_chained(self) -> None:
        """Test chained tracebacks."""
        cause = Traceback(exception_type="IOError", message="file not found")
        tb = Traceback(
            exception_type="RuntimeError",
            message="operation failed",
            chained=[cause],
        )
        assert tb.chained is not None
        assert len(tb.chained) == 1
        assert tb.chained[0].exception_type == "IOError"


class TestCaptureOutput:
    """Test CaptureOutput model."""

    def test_capture_output_defaults(self) -> None:
        """Test default values."""
        capture = CaptureOutput()
        assert capture.stdout == ""
        assert capture.stderr == ""
        assert capture.exit_code == 0
        assert capture.duration_ms == 0
        assert capture.timed_out is False
        assert capture.truncated is False

    def test_capture_output_with_data(self) -> None:
        """Test with actual output data."""
        capture = CaptureOutput(
            stdout="hello world\n",
            stderr="warning: something\n",
            exit_code=1,
            duration_ms=1500,
            command=["python", "-c", "print('hi')"],
            timed_out=False,
            truncated=False,
        )
        assert capture.stdout == "hello world\n"
        assert capture.exit_code == 1
        assert capture.duration_ms == 1500

    def test_capture_output_timed_out(self) -> None:
        """Test timeout capture."""
        capture = CaptureOutput(
            stdout="partial output",
            timed_out=True,
            truncated=True,
        )
        assert capture.timed_out is True
        assert capture.truncated is True


class TestGitInfo:
    """Test GitInfo model."""

    def test_git_info_creation(self) -> None:
        """Test creating git info."""
        git = GitInfo(
            ref="abc123",
            branch="main",
            dirty=False,
        )
        assert git.ref == "abc123"
        assert git.branch == "main"
        assert git.dirty is False

    def test_git_info_dirty(self) -> None:
        """Test dirty repo state."""
        git = GitInfo(ref="def456", branch="feature", dirty=True)
        assert git.dirty is True

    def test_git_info_with_remote(self) -> None:
        """Test git info with remote URL."""
        git = GitInfo(ref="123", remote_url="https://github.com/user/repo")
        assert git.remote_url == "https://github.com/user/repo"


class TestEnvironment:
    """Test Environment model."""

    def test_environment_creation(self) -> None:
        """Test creating environment info."""
        env = Environment(
            python_version="3.10.0",
            platform="linux",
            cwd="/home/user/project",
        )
        assert env.python_version == "3.10.0"
        assert env.platform == "linux"

    def test_environment_with_packages(self) -> None:
        """Test with installed packages."""
        packages = [
            PackageInfo(name="requests", version="2.28.0"),
            PackageInfo(name="pytest", version="7.0.0"),
        ]
        env = Environment(
            python_version="3.11.0",
            platform="darwin",
            cwd="/tmp",
            packages=packages,
        )
        assert len(env.packages) == 2
        assert env.packages[0].name == "requests"

    def test_environment_with_git(self) -> None:
        """Test with git info."""
        env = Environment(
            python_version="3.10.0",
            platform="win32",
            cwd="C:\\project",
            git=GitInfo(ref="123", branch="main", dirty=False),
        )
        assert env.git is not None
        assert env.git.ref == "123"


class TestBundleMetadata:
    """Test BundleMetadata model."""

    def test_metadata_creation(self) -> None:
        """Test creating metadata."""
        now = datetime.now()
        meta = BundleMetadata(
            version=BUNDLE_VERSION,
            created_at=now,
            command=["echo", "test"],
        )
        assert meta.version == BUNDLE_VERSION
        assert meta.created_at == now

    def test_metadata_defaults(self) -> None:
        """Test metadata default values."""
        meta = BundleMetadata()
        assert meta.version == BUNDLE_VERSION
        assert meta.bugsafe_version is not None
        assert meta.created_at is not None


class TestBugBundle:
    """Test BugBundle model."""

    def test_bundle_creation(self) -> None:
        """Test creating a complete bundle."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version=BUNDLE_VERSION,
                created_at=datetime.now(),
                command=["python", "script.py"],
            ),
            capture=CaptureOutput(
                stdout="output",
                stderr="",
                exit_code=0,
                duration_ms=100,
            ),
        )
        assert bundle.metadata.version == BUNDLE_VERSION
        assert bundle.capture.stdout == "output"

    def test_bundle_with_traceback(self) -> None:
        """Test bundle with traceback."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version=BUNDLE_VERSION,
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(exit_code=1),
            traceback=Traceback(
                exception_type="Exception",
                message="test error",
            ),
        )
        assert bundle.traceback is not None
        assert bundle.traceback.exception_type == "Exception"

    def test_bundle_with_redaction_report(self) -> None:
        """Test bundle with redaction report."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version=BUNDLE_VERSION,
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(),
            redaction_report={"AWS_KEY": 2, "GITHUB_TOKEN": 1},
        )
        assert bundle.redaction_report["AWS_KEY"] == 2

    def test_bundle_to_dict(self) -> None:
        """Test bundle serialization."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version=BUNDLE_VERSION,
                created_at=datetime.now(),
            ),
            capture=CaptureOutput(stdout="test"),
        )
        data = bundle.to_dict()
        assert "metadata" in data
        assert "capture" in data
        assert data["metadata"]["version"] == BUNDLE_VERSION

    def test_bundle_from_dict(self) -> None:
        """Test bundle deserialization."""
        data = {
            "version": BUNDLE_VERSION,
            "metadata": {
                "version": BUNDLE_VERSION,
                "created_at": datetime.now().isoformat(),
                "command": ["echo"],
            },
            "capture": {
                "stdout": "hello",
                "stderr": "",
                "exit_code": 0,
                "duration_ms": 50,
                "timed_out": False,
                "truncated": False,
            },
        }
        bundle = BugBundle.from_dict(data)
        assert bundle.capture.stdout == "hello"
