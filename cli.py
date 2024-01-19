import csv

from collections import defaultdict
from datetime import datetime, timezone as tz, timedelta
from pathlib import Path

import pendulum

from minicli import cli, run

DEFAULT_PATH = "data/Kindle.Devices.ReadingSession/Kindle.Devices.ReadingSession.csv"


@cli
def compute(path: Path = Path(DEFAULT_PATH), timezone="Europe/Paris"):
    results = defaultdict(lambda: datetime.utcfromtimestamp(0).replace(tzinfo=tz.utc))
    orphans = {}

    # TODO:
    # - compute total reading time
    #   - take min(start_timestamp) if start_timestamp.hour > 6
    #   - make 6 a variable (used also for next day search)
    # - refactor by grouping by date first
    # - do timezone conversion before comparing hour > 6 or < 6

    # BOM in input CSV...
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]

    for row in rows:
        try:
            start = datetime.fromisoformat(row["start_timestamp"])
        except ValueError:
            print(f"No start date for row {row}")
            end = datetime.fromisoformat(row["end_timestamp"])
            if (
                end.date() in orphans and orphans[end.date()] < end
            ) or end.date() not in orphans:
                orphans[end.date()] = end
        else:
            end = datetime.fromisoformat(row["end_timestamp"])
            if results[start.date()] < end:
                results[start.date()] = end

    results = dict(sorted(results.items()))

    for today in results:
        tomorrow = today + timedelta(days=1)
        # look for a suitable orphan, same day
        if today in orphans and orphans[today] > results[today]:
            results[today] = orphans[today]
        # and/or an early enough orphan for the next day
        if (
            tomorrow in orphans
            and orphans[tomorrow] > results[today]
            and orphans[tomorrow].hour < 6
        ):
            print(f"Gotcha, tomorrow orphan {orphans[tomorrow]} as of {today}")
            results[today] = orphans[tomorrow]
        print(f"{today}\t{results[today]}")

    def to_local_dt(dt):
        return pendulum.instance(dt).in_timezone(timezone)

    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    output_file = output_path / f"{datetime.today().date().isoformat()}.csv"
    with Path(output_file).open("w") as f:
        writer = csv.DictWriter(f, fieldnames=["day", "asleep_datetime", "asleep_datetime_utc"])
        writer.writeheader()
        writer.writerows(
            [
                {"day": k, "asleep_datetime": to_local_dt(v), "asleep_datetime_utc": v}
                for k, v in results.items()
            ]
        )
    print(f"Results written to {output_file}, with timezone {timezone}")


if __name__ == "__main__":
    run()
