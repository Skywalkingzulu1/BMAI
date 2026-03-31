import logging
import sys
from pathlib import Path
from typing import List

# Import the detection utility that scans the repository for self‑modifications.
# This function returns a list of human‑readable issue strings.
from check_self_mod import detect_self_modifications

# Configure a module‑level logger. In production, the logging configuration
# should be set up by the orchestrating system (e.g., Docker, systemd, or the
# hosting platform). Here we fall back to a basic configuration that logs to
# stderr.
logger = logging.getLogger("self_mod_monitor")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def monitor_self_modifications(repo_root: Path | None = None) -> List[str]:
    """Run the self‑modification detection and return any issues.

    Parameters
    ----------
    repo_root: Path | None
        The root directory of the repository to scan. If ``None`` the function
        determines the project root relative to this file (two levels up).

    Returns
    -------
    List[str]
        A list of issue messages. An empty list indicates no unexpected changes.
    """
    if repo_root is None:
        # ``monitor_self_mod.py`` lives at the project root, so ``Path(__file__)``
        # points to the file itself. Its parent directory is the repository root.
        repo_root = Path(__file__).parent
    issues = detect_self_modifications(repo_root)
    return issues


def alert_issues(issues: List[str]) -> None:
    """Log and alert on detected self‑modification issues.

    Currently the alert mechanism is a warning log entry. In a real production
    environment this could be extended to send emails, push notifications, or
    integrate with monitoring tools like Prometheus, Datadog, etc.
    """
    if not issues:
        logger.info("No self‑modifications detected.")
        return

    for issue in issues:
        logger.warning("Self‑modification detected: %s", issue)

    # Placeholder for additional alerting (e.g., email, webhook).
    # Example:
    # send_alert_via_webhook(issues)


def main() -> None:
    """Entry point for the monitoring script.

    This function is intended to be executed as a long‑running background
    process (e.g., via ``nohup`` or a systemd service) or scheduled periodically
    (e.g., with cron). It runs the detection once and exits with a non‑zero
    status code if any issues are found, allowing orchestration tools to react.
    """
    issues = monitor_self_modifications()
    alert_issues(issues)
    if issues:
        # Exit with a non‑zero code to signal failure to the supervising process.
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
