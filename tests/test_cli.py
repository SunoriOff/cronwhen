import json
from datetime import timedelta

from cronwhen.cli import main, relative, split_crontab_line


def test_relative():
    assert relative(timedelta(seconds=10)) == "now"
    assert relative(timedelta(minutes=5)) == "in 5 min"
    assert relative(timedelta(hours=2, minutes=10)) == "in 2h 10m"
    assert relative(timedelta(hours=3)) == "in 3h"
    assert relative(timedelta(days=2, hours=1)) == "in 2 days"


def test_basic_output(capsys):
    assert main(["*/15", "*", "*", "*", "*", "--from", "2026-11-02 13:04", "-n", "2"]) == 0
    out = capsys.readouterr().out
    assert "Every 15 minutes" in out
    assert "Mon 2026-11-02 13:15" in out
    assert "in 11 min" in out


def test_json_output(capsys):
    main(["0 9 * * 1-5", "--from", "2026-11-06 10:00", "-n", "2", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["description"] == "At 09:00, on Monday through Friday"
    assert data["next_runs"] == ["2026-11-09T09:00", "2026-11-10T09:00"]


def test_invalid_expression(capsys):
    assert main(["99 * * * *"]) == 2
    assert "out of range" in capsys.readouterr().err


def test_no_args(capsys):
    assert main([]) == 2


def test_bad_from(capsys):
    assert main(["* * * * *", "--from", "yesterday"]) == 2


def test_split_crontab_line():
    assert split_crontab_line("# comment") is None
    assert split_crontab_line("MAILTO=me@example.com") is None
    assert split_crontab_line("") is None
    assert split_crontab_line("*/5 * * * * /usr/bin/job --flag") == ("*/5 * * * *", "/usr/bin/job --flag")
    assert split_crontab_line("@daily backup.sh") == ("@daily", "backup.sh")


def test_crontab_file(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text("MAILTO=me\n# backup\n0 2 * * * /bin/backup\n61 * * * * /bin/bad\n")
    assert main(["--file", str(f)]) == 1
    out = capsys.readouterr().out
    assert "At 02:00, every day" in out
    assert "$ /bin/backup" in out
    assert "ERROR" in out
