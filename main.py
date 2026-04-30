import argparse
import logging
import sys
import io

# Force UTF-8 encoding for Windows terminals to prevent emoji crashes
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from db.database import setup_db, save_scan, save_resource, save_alert
from data_source import get_findings, get_ai_advice
from analyzer.cost_estimator import estimate_total, get_breakdown_by_type
from analyzer.reporter import print_report, build_report_text
from actor.cleaner import cleanup_resource
from notifier.budget_alert import check_budget, send_alert_email
from config import BUDGET_THRESHOLD

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("optimizer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_scan():
    """Run scan against your real AWS account."""
    console.print(f"[bold blue]Running scan in AWS mode...[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Scanning (AWS)...", total=1)
        findings = get_findings()
        progress.advance(task)

    logger.info(f"Scan complete (AWS): {len(findings)} resources found")
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="☁️  AWS Smart Cost Optimizer — Find and eliminate cloud waste",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --scan              Scan for wasted resources
  python main.py --scan --ai         Scan + get AI recommendations
  python main.py --scan --dry-run    Preview what would be deleted
  python main.py --scan --execute    Delete wasted resources (with confirmation)
  python main.py --dashboard         Launch the web dashboard
    python main.py --optimize          Run autonomous optimization
    python main.py --optimize --auto-apply  Optimize and apply actions
        """
    )
    parser.add_argument("--scan", action="store_true", help="Run a full scan of your AWS account")
    parser.add_argument("--dry-run", action="store_true", help="Show what actions would be taken (safe)")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup actions (asks for confirmation)")
    parser.add_argument("--ai", action="store_true", help="Get AI-powered recommendations via Ollama")
    parser.add_argument("--dashboard", action="store_true", help="Launch the web dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the dashboard on (default: 5000)")
    parser.add_argument("--optimize", action="store_true", help="Run autonomous optimization pipeline")
    parser.add_argument("--auto-apply", action="store_true", help="Apply optimization actions automatically")
    parser.add_argument("--optimize-lookback-days", type=int, help="Lookback window for metrics")
    parser.add_argument("--optimize-horizon-hours", type=int, help="Forecast horizon in hours")
    parser.add_argument("--optimize-max-resources", type=int, help="Limit resources monitored per run")
    args = parser.parse_args()

    # Show banner
    console.print(Panel(
        "[bold cyan]☁️  AWS Smart Cost Optimizer[/bold cyan]\n"
        "[dim]Find waste. Save money. Sleep better.[/dim]",
        border_style="bright_cyan"
    ))

    setup_db()

    if args.dashboard:
        from dashboard.app import start_dashboard
        start_dashboard(port=args.port)
        return

    if args.optimize:
        from optimizer.pipeline import run_autonomous_optimizer
        console.print()
        summary = run_autonomous_optimizer(
            auto_apply=args.auto_apply,
            lookback_days=args.optimize_lookback_days,
            horizon_hours=args.optimize_horizon_hours,
            max_resources=args.optimize_max_resources,
        )
        console.print(Panel(
            f"Optimization run complete. Resources: {summary['resources']} | "
            f"Metrics: {summary['metrics']} | Forecasts: {summary['forecasts']} | "
            f"RL: {summary.get('rl_decisions', 0)} (↑{summary.get('scale_up', 0)} • "
            f"→{summary.get('maintain', 0)} • ↓{summary.get('scale_down', 0)}) | "
            f"Actions: {summary['actions']} | Applied: {summary['applied']}",
            title="Optimizer Summary",
            border_style="bright_green"
        ))
        return

    if not args.scan and not args.dashboard:
        parser.print_help()
        return

    if args.scan:
        console.print()
        findings = run_scan()
        total = estimate_total(findings)

        # Print the report
        print_report(findings, total)

        # Show breakdown
        if findings:
            breakdown = get_breakdown_by_type(findings)
            console.print()
            console.print("[bold]📊 Waste Breakdown by Service:[/bold]")
            for svc, cost in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                bar_len = int(cost / total * 30) if total > 0 else 0
                bar = "█" * bar_len
                console.print(f"  [cyan]{svc:12}[/cyan] [red]{bar}[/red] ${cost:.2f}")

        # Save to database
        scan_id = save_scan(total, len(findings))
        for f in findings:
            save_resource(scan_id, f["type"], f["id"], f["detail"], f["waste_usd"], f["region"])

        # Budget check
        console.print()
        budget = check_budget(total, findings)
        if budget["exceeded"]:
            console.print(Panel(
                f"[bold red]BUDGET ALERT: ${budget['total_waste']:.2f} exceeds "
                f"threshold of ${budget['threshold']:.2f} (+${budget['overage']:.2f})[/bold red]\n"
                f"[yellow]Usage: {budget['percentage']:.1f}% of budget[/yellow]",
                title="Budget Alert",
                border_style="bright_red"
            ))
            to_email = None
            try:
                from db.database import get_connection
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT email, alert_email FROM users LIMIT 1")
                    row = cursor.fetchone()
                    if row:
                        to_email = row["alert_email"] or row["email"]
            except Exception as e:
                pass
                
            email_sent = send_alert_email(budget, findings, to_email=to_email)
            save_alert("budget_exceeded",
                f"Waste ${budget['total_waste']:.2f} exceeds threshold ${budget['threshold']:.2f}",
                budget['total_waste'], budget['threshold'], email_sent)
            if email_sent:
                console.print("[green]  Alert email sent successfully.[/green]")
            else:
                console.print("[dim]  Email not sent (configure SMTP in .env to enable).[/dim]")
        else:
            console.print(Panel(
                f"[bold green]Budget OK: ${budget['total_waste']:.2f} / "
                f"${budget['threshold']:.2f} ({budget['percentage']:.1f}%)[/bold green]",
                title="Budget Status",
                border_style="green"
            ))

        # AI advice
        if args.ai:
            console.print()
            console.print(Panel("[bold]🤖 Asking AI for recommendations...[/bold]", border_style="bright_magenta"))
            report_text = build_report_text(findings, total)
            advice = get_ai_advice(report_text)
            if advice and scan_id:
                try:
                    from db.database import update_scan_ai_advice
                    update_scan_ai_advice(scan_id, advice)
                    logger.info("AI advice saved to database.")
                except Exception as e:
                    logger.warning(f"Failed to save AI advice: {e}")
            console.print()
            console.print(Panel(advice, title="🤖 AI Recommendation", border_style="bright_magenta"))

        # Dry run
        if args.dry_run and findings:
            console.print()
            console.print(Panel("[bold yellow]🧪 Dry Run — No changes will be made[/bold yellow]", border_style="yellow"))
            for f in findings:
                cleanup_resource(f, dry_run=True)

        # Execute
        if args.execute and findings:
            console.print()
            console.print("[bold red]⚠️  WARNING: This will permanently delete resources![/bold red]")
            confirm = console.input("[bold]Type 'yes' to confirm: [/bold]")
            if confirm.strip().lower() == "yes":
                console.print()
                success = 0
                for f in findings:
                    try:
                        if cleanup_resource(f, dry_run=False):
                            success += 1
                    except Exception as e:
                        logger.error(f"Cleanup failed for {f.get('id')}: {e}")
                        console.print(f"[red]  Error cleaning up {f.get('id')}: {e}[/red]")
                console.print(Panel(
                    f"[bold green]✅ Cleaned up {success}/{len(findings)} resources[/bold green]",
                    border_style="green"
                ))
            else:
                console.print("[yellow]Cleanup cancelled.[/yellow]")

        console.print()
        logger.info("Scan complete.")


if __name__ == "__main__":
    main()
