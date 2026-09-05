import threading
import time
import unittest

from mssql_database_documenter.web.job_manager import JobConflictError, JobManager


class JobManagerTests(unittest.TestCase):
    def test_successful_job_reaches_completed_status(self) -> None:
        manager = JobManager()

        def target(job, update):
            update({"prompt": "20", "stage": "finalize", "status": "PASS", "database": "School"})
            return {"warning_count": 0, "result": "ready"}

        finished = manager.wait(manager.start("metadata", "School", "metadata", target).id)
        self.assertEqual(finished.status, "COMPLETED")
        self.assertEqual(finished.progress, 100)
        self.assertTrue(finished.started_utc)
        self.assertTrue(finished.finished_utc)
        self.assertEqual(finished.result["result"], "ready")

    def test_one_job_lock_and_stage_boundary_cancellation(self) -> None:
        manager = JobManager(sensitive_values=("private-server",))
        entered = threading.Event()

        def target(job, update):
            entered.set()
            update({"prompt": "02", "stage": "security", "status": "PASS", "database": "School"})
            while not job.cancel_event.is_set():
                time.sleep(0.005)
            return {"warning_count": 0}

        job = manager.start("metadata", "School", "metadata", target)
        self.assertTrue(entered.wait(1))
        with self.assertRaises(JobConflictError):
            manager.start("metadata", "School", "metadata", target)
        manager.cancel(job.id)
        finished = manager.wait(job.id)
        self.assertEqual(finished.status, "CANCELLED")
        self.assertIn("next safe stage boundary", " ".join(finished.logs))

    def test_logs_are_redacted(self) -> None:
        manager = JobManager(sensitive_values=("private-server",))

        def target(job, update):
            raise RuntimeError("private-server password=bad")

        finished = manager.wait(manager.start("dry-run", "School", "metadata", target).id)
        self.assertEqual(finished.status, "FAILED")
        self.assertTrue(finished.error)
        text = " ".join(finished.logs)
        self.assertNotIn("private-server", text)
        self.assertNotIn("password=bad", text)
        public = finished.public()
        for field in ("id", "database", "mode", "status", "current_stage", "progress", "started_utc", "finished_utc", "elapsed_seconds", "warnings", "error", "logs"):
            self.assertIn(field, public)


if __name__ == "__main__":
    unittest.main()
