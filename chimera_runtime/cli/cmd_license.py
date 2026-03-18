"""
chimera-runtime CLI — License Management

Usage:
    chimera-runtime license status       # Show current license tier
    chimera-runtime license activate     # Activate a license key
    chimera-runtime license deactivate   # Remove stored license key
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(stderr=True)


@click.group("license")
def license_cmd():
    """Manage your Chimera license key."""
    pass


@license_cmd.command("status")
def license_status():
    """Show current license tier and details."""
    from ..licensing import get_license, reset_license

    # Force fresh resolution
    reset_license()
    lic = get_license()

    tier_colors = {"free": "white", "pro": "cyan", "enterprise": "yellow"}
    tier_icons = {"free": "🆓", "pro": "⚡", "enterprise": "👑"}

    color = tier_colors.get(lic.tier_name, "white")
    icon = tier_icons.get(lic.tier_name, "")

    table = Table(show_header=False, border_style="dim", padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value", style=f"bold {color}")

    table.add_row("Tier", f"{icon} {lic.tier_name.upper()}")

    if lic.email:
        table.add_row("Email", lic.email)
    if lic.org:
        table.add_row("Organization", lic.org)
    if lic.expires_at > 0:
        exp = datetime.fromtimestamp(lic.expires_at, tz=timezone.utc)
        expired_str = " [red](EXPIRED)[/red]" if lic.is_expired else ""
        table.add_row("Expires", f"{exp.strftime('%Y-%m-%d')}{expired_str}")
    if lic.features:
        table.add_row("Features", ", ".join(lic.features))

    # Show resolution source
    import os
    if lic.raw_token:
        if os.environ.get("CHIMERA_LICENSE_KEY", "").strip():
            source = "CHIMERA_LICENSE_KEY env var"
        else:
            source = ".chimera/license.key file"
        table.add_row("Source", source)
    else:
        table.add_row("Source", "Default (no key)")

    console.print(Panel(table, title="[bold]Chimera License[/bold]", border_style=color))

    if lic.tier_name == "free":
        console.print()
        console.print(
            "[dim]Upgrade at [bold]https://runtime.chimera-protocol.com/settings[/bold] "
            "for Pro/Enterprise features.[/dim]"
        )


@license_cmd.command("activate")
@click.argument("key", required=False)
def license_activate(key):
    """Activate a license key.

    Provide the key as an argument or paste it when prompted.
    The key will be saved to .chimera/license.key for future use.
    """
    if not key:
        key = click.prompt("Paste your license key", hide_input=False).strip()

    if not key:
        console.print("[red]No key provided.[/red]")
        raise SystemExit(1)

    # Validate the key
    try:
        from ..licensing import activate_license
        lic = activate_license(key)
    except Exception as exc:
        console.print(f"[red]Invalid key:[/red] {exc}")
        raise SystemExit(1)

    # Save to .chimera/license.key
    key_dir = Path(".chimera")
    key_dir.mkdir(parents=True, exist_ok=True)
    key_path = key_dir / "license.key"
    key_path.write_text(key, encoding="utf-8")

    tier_icons = {"free": "🆓", "pro": "⚡", "enterprise": "👑"}
    icon = tier_icons.get(lic.tier_name, "")

    console.print(f"[green]License activated![/green] {icon} {lic.tier_name.upper()}")
    if lic.email:
        console.print(f"[dim]Email: {lic.email}[/dim]")
    console.print(f"[dim]Saved to {key_path}[/dim]")


@license_cmd.command("deactivate")
def license_deactivate():
    """Remove stored license key."""
    from ..licensing import reset_license

    removed = False
    for path in [
        Path(".chimera") / "license.key",
        Path.home() / ".chimera" / "license.key",
    ]:
        if path.exists():
            path.unlink()
            console.print(f"[yellow]Removed:[/yellow] {path}")
            removed = True

    reset_license()

    if removed:
        console.print("[green]License deactivated. Reverted to FREE tier.[/green]")
    else:
        console.print("[dim]No license key found to remove.[/dim]")
