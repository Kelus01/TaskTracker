import sqlite3
import statistics
import time

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Compare the project/status/due-date query plan with and without its index."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=100_000)
        parser.add_argument("--samples", type=int, default=15)

    def handle(self, *args, **options):
        rows = options["rows"]
        samples = options["samples"]
        if not 1_000 <= rows <= 1_000_000:
            raise CommandError("--rows must be between 1000 and 1000000.")
        if not 3 <= samples <= 100:
            raise CommandError("--samples must be between 3 and 100.")

        with sqlite3.connect(":memory:") as database:
            database.execute(
                """
                CREATE TABLE task_benchmark (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    due_date TEXT
                )
                """
            )
            database.executemany(
                "INSERT INTO task_benchmark VALUES (?, ?, ?, ?)",
                (
                    (
                        task_id,
                        task_id % 100,
                        ("todo", "in_progress", "done")[(task_id // 100) % 3],
                        f"2027-{task_id % 12 + 1:02}-01",
                    )
                    for task_id in range(1, rows + 1)
                ),
            )

            indexed_query = (
                "SELECT id, due_date FROM task_benchmark "
                "WHERE project_id = ? AND status = ? "
                "ORDER BY due_date, id LIMIT 20"
            )
            baseline_query = (
                "SELECT id, due_date FROM task_benchmark NOT INDEXED "
                "WHERE project_id = ? AND status = ? "
                "ORDER BY due_date, id LIMIT 20"
            )
            parameters = (42, "todo")
            baseline_plan = self._query_plan(database, baseline_query, parameters)

            database.execute(
                "CREATE INDEX task_proj_status_due_id_idx "
                "ON task_benchmark (project_id, status, due_date, id)"
            )
            database.execute("ANALYZE")
            indexed_plan = self._query_plan(database, indexed_query, parameters)

            baseline_result = database.execute(baseline_query, parameters).fetchall()
            indexed_result = database.execute(indexed_query, parameters).fetchall()
            if baseline_result != indexed_result:
                raise CommandError("Indexed query returned different results.")

            baseline_times = self._measure(database, baseline_query, parameters, samples)
            indexed_times = self._measure(database, indexed_query, parameters, samples)

        baseline_ms = statistics.median(baseline_times) * 1000
        indexed_ms = statistics.median(indexed_times) * 1000
        improvement = baseline_ms / indexed_ms if indexed_ms else float("inf")

        self.stdout.write(f"Rows: {rows:,}; samples: {samples}")
        self.stdout.write("Plan without index:")
        for line in baseline_plan:
            self.stdout.write(f"  {line}")
        self.stdout.write("Plan with task_proj_status_due_id_idx:")
        for line in indexed_plan:
            self.stdout.write(f"  {line}")
        self.stdout.write(f"Median without index: {baseline_ms:.3f} ms")
        self.stdout.write(f"Median with index: {indexed_ms:.3f} ms")
        self.stdout.write(f"Measured speedup: {improvement:.2f}x")

    @staticmethod
    def _query_plan(database, query, parameters):
        return [
            row[3]
            for row in database.execute(
                f"EXPLAIN QUERY PLAN {query}",
                parameters,
            ).fetchall()
        ]

    @staticmethod
    def _measure(database, query, parameters, samples):
        durations = []
        for _ in range(samples):
            started_at = time.perf_counter()
            database.execute(query, parameters).fetchall()
            durations.append(time.perf_counter() - started_at)
        return durations
