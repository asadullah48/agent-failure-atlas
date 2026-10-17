import unittest

from atlas.core import AMOUNT, LostResponse, World, evaluate, run_case, verify_report


class CaseTests(unittest.TestCase):
    def test_vulnerable_reproduces_duplicate(self):
        report = run_case("vulnerable", True)
        self.assertEqual(report["state"]["order_count"], 2)
        self.assertEqual(report["state"]["spent_minor"], 2 * AMOUNT)
        self.assertEqual(report["verdict"], "fail")

    def test_repaired_reconciles_without_duplicate(self):
        report = run_case("repaired", True)
        self.assertEqual(report["state"]["order_count"], 1)
        self.assertEqual(report["state"]["spent_minor"], AMOUNT)
        self.assertEqual(report["verdict"], "pass")
        self.assertTrue(any(e["payload"].get("tool") == "get_purchase_order_by_intent"
                            for e in report["events"]))

    def test_no_fault_both_pass(self):
        for mode in ["vulnerable", "repaired"]:
            with self.subTest(mode=mode):
                self.assertEqual(run_case(mode, False)["verdict"], "pass")

    def test_deterministic_reproduction(self):
        self.assertEqual(run_case("repaired"), run_case("repaired"))

    def test_hash_detects_edit(self):
        report = run_case()
        self.assertTrue(verify_report(report))
        report["events"][0]["payload"]["amount_minor"] = 999
        self.assertFalse(verify_report(report))

    def test_lost_response_really_commits(self):
        w = World("repaired", True)
        self.addCleanup(w.db.close)
        with self.assertRaises(LostResponse):
            w.create_order("key")
        self.assertEqual(w.state()["order_count"], 1)

    def test_repaired_retries_and_changed_key_do_not_duplicate(self):
        w = World("repaired", False)
        self.addCleanup(w.db.close)
        first = w.create_order("key")
        self.assertEqual(w.create_order("key"), first)
        self.assertEqual(w.create_order("new-key"), first)
        self.assertEqual(w.state()["spent_minor"], AMOUNT)
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_CONFLICT"):
            w.create_order("key", AMOUNT + 1)

    def test_invalid_approval_cannot_commit(self):
        w = World("repaired", False)
        self.addCleanup(w.db.close)
        w.approved = False
        with self.assertRaisesRegex(ValueError, "APPROVAL_INVALID"):
            w.create_order("key")
        self.assertEqual(w.state()["spent_minor"], 0)

    def test_evaluator_detects_corrupt_ledger(self):
        w = World("repaired", False)
        self.addCleanup(w.db.close)
        w.create_order("key")
        w.db.execute("UPDATE budget SET spent=0")
        assertions = {a["id"]: a["status"] for a in evaluate(w)}
        self.assertEqual(assertions["ledger_balances"], "fail")

    def test_evaluator_detects_missing_commit_evidence(self):
        w = World("repaired", False)
        self.addCleanup(w.db.close)
        w.create_order("key")
        w.db.execute("DELETE FROM events WHERE kind='purchase.committed'")
        assertions = {a["id"]: a["status"] for a in evaluate(w)}
        self.assertEqual(assertions["commit_evidence"], "fail")


if __name__ == "__main__":
    unittest.main()
