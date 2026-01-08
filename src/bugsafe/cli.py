"""CLI commands for bugsafe."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bugsafe import __version__

app = typer.Typer(
    name="bugsafe",
    help="Safe-to-share crash bundles for humans and LLMs",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"bugsafe version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """bugsafe - Safe-to-share crash bundles for humans and LLMs."""


@app.command()
def run(
    command: Annotated[
        list[str],
        typer.Argument(help="Command to execute"),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output bundle path"),
    ] = None,
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", help="Timeout in seconds"),
    ] = 300,
    attach: Annotated[
        list[Path] | None,
        typer.Option("--attach", "-a", help="Files to attach"),
    ] = None,
    no_redact: Annotated[
        bool,
        typer.Option("--no-redact", help="Skip redaction"),
    ] = False,
) -> None:
    """Run a command and capture crash information into a bundle."""
    from bugsafe.bundle.schema import (
        BugBundle,
        BundleMetadata,
        CaptureOutput,
        Environment,
        Frame,
        GitInfo,
        PackageInfo,
        Traceback,
    )
    from bugsafe.bundle.writer import add_attachment, create_bundle
    from bugsafe.capture.environment import EnvConfig, collect_environment
    from bugsafe.capture.runner import CaptureConfig
    from bugsafe.capture.runner import run_command as capture_run
    from bugsafe.capture.traceback import extract_traceback
    from bugsafe.redact.engine import create_redaction_engine

    if output is None:
        output = Path("./bug.bugbundle")

    with console.status("[bold blue]Running command..."):
        config = CaptureConfig(timeout=timeout)
        result = capture_run(command, config)

    with console.status("[bold blue]Collecting environment..."):
        env_config = EnvConfig()
        env_snapshot = collect_environment(env_config)

    tb = None
    if result.stderr:
        parsed_tb = extract_traceback(result.stderr)
        if parsed_tb:
            tb = Traceback(
                exception_type=parsed_tb.exception_type,
                message=parsed_tb.message,
                frames=[
                    Frame(
                        file=f.file,
                        line=f.line,
                        function=f.function,
                        code=f.code,
                        locals=f.locals if f.locals else None,
                    )
                    for f in parsed_tb.frames
                ],
            )

    capture = CaptureOutput(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        command=command,
        timed_out=result.timed_out,
        truncated=result.truncated_stdout or result.truncated_stderr,
    )

    git_info = None
    if env_snapshot.git:
        git_info = GitInfo(
            ref=env_snapshot.git.ref,
            branch=env_snapshot.git.branch,
            dirty=env_snapshot.git.dirty,
            remote_url=env_snapshot.git.remote_url,
        )

    environment = Environment(
        python_version=env_snapshot.python_version,
        python_executable=env_snapshot.python_executable,
        platform=env_snapshot.platform,
        packages=[
            PackageInfo(name=p.name, version=p.version) for p in env_snapshot.packages
        ],
        env_vars=env_snapshot.env_vars,
        cwd=env_snapshot.cwd,
        git=git_info,
        virtualenv=env_snapshot.virtualenv,
        in_container=env_snapshot.in_container,
        ci_detected=env_snapshot.ci_detected,
    )

    redaction_report: dict[str, int] = {}
    if not no_redact:
        with console.status("[bold blue]Redacting secrets..."):
            engine = create_redaction_engine()

            capture_stdout, _ = engine.redact(capture.stdout)
            capture_stderr, _ = engine.redact(capture.stderr)

            capture = CaptureOutput(
                stdout=capture_stdout,
                stderr=capture_stderr,
                exit_code=capture.exit_code,
                duration_ms=capture.duration_ms,
                command=capture.command,
                timed_out=capture.timed_out,
                truncated=capture.truncated,
            )

            redaction_report = engine.get_redaction_summary()

    bundle = BugBundle(
        metadata=BundleMetadata(
            created_at=datetime.utcnow(),
            bugsafe_version=__version__,
            redaction_salt_hash=engine.get_salt_hash() if not no_redact else "",
        ),
        capture=capture,
        traceback=tb,
        environment=environment,
        redaction_report=redaction_report,
    )

    with console.status("[bold blue]Writing bundle..."):
        create_bundle(bundle, output)

        if attach:
            for file_path in attach:
                if file_path.exists():
                    content = file_path.read_text()
                    add_attachment(output, file_path.name, content)

    console.print(f"\n[bold green]✓[/bold green] Bundle created: {output}")
    console.print(f"  Exit code: {result.exit_code}")
    console.print(f"  Duration: {result.duration_ms}ms")

    if redaction_report:
        total = sum(redaction_report.values())
        console.print(f"  Redacted: {total} secrets")

    if result.timed_out:
        console.print("  [yellow]⚠ Command timed out[/yellow]")


@app.command()
def render(
    bundle_path: Annotated[
        Path,
        typer.Argument(help="Path to .bugbundle file"),
    ],
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: md or json"),
    ] = "md",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    llm: Annotated[
        bool,
        typer.Option("--llm", help="Optimize output for LLM context"),
    ] = False,
    max_tokens: Annotated[
        int,
        typer.Option("--max-tokens", help="Max tokens for LLM output"),
    ] = 4000,
) -> None:
    """Render a bundle to Markdown or JSON."""
    from bugsafe.bundle.reader import read_bundle
    from bugsafe.render.json_export import to_json, to_llm_context
    from bugsafe.render.markdown import render_markdown

    if not bundle_path.exists():
        console.print(f"[red]Error:[/red] Bundle not found: {bundle_path}")
        raise typer.Exit(1)

    bundle = read_bundle(bundle_path)

    if format == "json":
        if llm:
            result = to_llm_context(bundle, max_tokens=max_tokens)
        else:
            result = to_json(bundle)
    else:
        result = render_markdown(bundle)

    if output:
        output.write_text(result)
        console.print(f"[green]✓[/green] Output written to: {output}")
    else:
        console.print(result)


@app.command()
def inspect(
    bundle_path: Annotated[
        Path,
        typer.Argument(help="Path to .bugbundle file"),
    ],
) -> None:
    """Inspect bundle metadata and contents."""
    from bugsafe.bundle.reader import list_attachments, read_bundle, verify_integrity
    from bugsafe.bundle.writer import validate_bundle

    if not bundle_path.exists():
        console.print(f"[red]Error:[/red] Bundle not found: {bundle_path}")
        raise typer.Exit(1)

    validation = validate_bundle(bundle_path)
    if not validation.valid:
        console.print("[red]Bundle validation failed:[/red]")
        for error in validation.errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)

    bundle = read_bundle(bundle_path)
    integrity = verify_integrity(bundle_path)
    attachments = list_attachments(bundle_path)

    table = Table(title="Bundle Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", bundle.metadata.version)
    table.add_row("Created", str(bundle.metadata.created_at))
    table.add_row("bugsafe Version", bundle.metadata.bugsafe_version)
    table.add_row("Integrity", "✓ Valid" if integrity else "✗ Invalid")

    console.print(table)
    console.print()

    if bundle.capture.command:
        cmd_str = " ".join(bundle.capture.command)
        console.print(Panel(cmd_str, title="Command"))

    capture_table = Table(title="Capture")
    capture_table.add_column("Property", style="cyan")
    capture_table.add_column("Value")

    capture_table.add_row("Exit Code", str(bundle.capture.exit_code))
    capture_table.add_row("Duration", f"{bundle.capture.duration_ms}ms")
    capture_table.add_row("Timed Out", "Yes" if bundle.capture.timed_out else "No")
    capture_table.add_row("stdout length", f"{len(bundle.capture.stdout)} chars")
    capture_table.add_row("stderr length", f"{len(bundle.capture.stderr)} chars")

    console.print(capture_table)
    console.print()

    if bundle.traceback:
        console.print(
            Panel(
                f"{bundle.traceback.exception_type}: {bundle.traceback.message}",
                title="Error",
                border_style="red",
            )
        )
        console.print()

    if bundle.environment:
        env_table = Table(title="Environment")
        env_table.add_column("Property", style="cyan")
        env_table.add_column("Value")

        env_table.add_row("Python", bundle.environment.python_version)
        env_table.add_row("Platform", bundle.environment.platform)
        env_table.add_row("CWD", bundle.environment.cwd)
        env_table.add_row("Packages", str(len(bundle.environment.packages)))
        venv_status = "Yes" if bundle.environment.virtualenv else "No"
        env_table.add_row("Virtualenv", venv_status)

        if bundle.environment.git:
            ref = bundle.environment.git.ref or "N/A"
            env_table.add_row("Git Ref", ref[:7] if len(ref) > 7 else ref)

        console.print(env_table)
        console.print()

    if bundle.redaction_report:
        redact_table = Table(title="Redaction Summary")
        redact_table.add_column("Category", style="cyan")
        redact_table.add_column("Count", style="yellow")

        for category, count in sorted(bundle.redaction_report.items()):
            redact_table.add_row(category, str(count))

        total = sum(bundle.redaction_report.values())
        redact_table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

        console.print(redact_table)
        console.print()

    if attachments:
        console.print(f"[bold]Attachments ({len(attachments)}):[/bold]")
        for att in attachments:
            console.print(f"  - {att}")


@app.command()
def config(
    show: Annotated[
        bool,
        typer.Option("--show", help="Show current configuration"),
    ] = False,
    path: Annotated[
        bool,
        typer.Option("--path", help="Show config file path"),
    ] = False,
    init: Annotated[
        bool,
        typer.Option("--init", help="Create default config file"),
    ] = False,
) -> None:
    """Manage bugsafe configuration."""
    from bugsafe.config import get_config_dir, get_config_file, load_config

    config_file = get_config_file()

    if path:
        console.print(f"Config file: {config_file}")
        console.print(f"Config dir: {get_config_dir()}")
        return

    if init:
        if config_file.exists():
            console.print(f"[yellow]Config file already exists:[/yellow] {config_file}")
            return

        config_file.parent.mkdir(parents=True, exist_ok=True)

        default_config = """\
# bugsafe configuration file

[defaults]
timeout = 300
# env_allowlist = ["PATH", "VIRTUAL_ENV", "PYTHONPATH"]

[redaction]
redact_emails = true
redact_ips = true
redact_uuids = false
# custom_patterns = "~/.config/bugsafe/patterns.yaml"

[output]
default_format = "md"
"""
        config_file.write_text(default_config)
        console.print(f"[green]✓[/green] Created config file: {config_file}")
        return

    if show or not (show or path or init):
        cfg = load_config()
        console.print(f"[bold]Config file:[/bold] {config_file}")
        console.print(f"[bold]Exists:[/bold] {config_file.exists()}")
        console.print()

        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("defaults.timeout", str(cfg.defaults.timeout))
        table.add_row("defaults.max_output_size", str(cfg.defaults.max_output_size))
        table.add_row("redaction.redact_emails", str(cfg.redaction.redact_emails))
        table.add_row("redaction.redact_ips", str(cfg.redaction.redact_ips))
        table.add_row("redaction.redact_uuids", str(cfg.redaction.redact_uuids))
        table.add_row("output.default_format", cfg.output.default_format)

        console.print(table)
