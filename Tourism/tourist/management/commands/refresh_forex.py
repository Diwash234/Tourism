"""Refresh official NRB exchange rates (run daily, e.g. cron at 00:30 NPT).

    python manage.py refresh_forex            # fetch last 7 days from NRB
    python manage.py refresh_forex --seed     # load dataset/nrb_forex_seed.json (offline)
"""

from django.core.management.base import BaseCommand, CommandError

from tourist import fx


class Command(BaseCommand):
    help = "Fetch Nepal Rastra Bank exchange rates into ForexRateSnapshot."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--seed", action="store_true", help="Load the bundled NRB seed file instead of fetching.")

    def handle(self, *args, **opts):
        if opts["seed"]:
            snaps = fx.load_seed_file()
        else:
            try:
                snaps = fx.fetch_from_nrb(days_back=opts["days"])
            except Exception as exc:
                raise CommandError(f"NRB fetch failed: {exc}. Existing snapshots are unchanged.")
        if not snaps:
            raise CommandError("No rates were stored.")
        latest = max(snaps, key=lambda s: s.rate_date)
        usd = fx.npr_per_unit(latest, "USD")
        self.stdout.write(self.style.SUCCESS(
            f"Stored {len(snaps)} NRB snapshot(s); latest {latest.rate_date} (USD buy {usd} NPR)."))
