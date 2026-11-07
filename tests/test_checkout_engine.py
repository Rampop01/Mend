import unittest
from services import checkout_engine


class TestCheckoutSettlementEngine(unittest.TestCase):
    def setUp(self) -> None:
        checkout_engine.init_db()

    def test_standard_usd_settlement(self) -> None:
        res = checkout_engine.process_settlement({
            "merchant_id": "merch_test_usd",
            "customer_email": "buyer@example.com",
            "currency": "USD",
            "gross_cents": 10000,
            "discount_cents": 0,
        })
        self.assertEqual(res.net_cents, 10000)
        self.assertEqual(res.platform_fee_cents, 320)
        self.assertAlmostEqual(res.effective_fee_bps, 320.0, places=2)
        self.assertEqual(res.status, "SETTLED")

    def test_partial_discount_eur_settlement(self) -> None:
        res = checkout_engine.process_settlement({
            "merchant_id": "merch_test_eur",
            "customer_email": "eu@example.com",
            "currency": "EUR",
            "gross_cents": 50000,
            "discount_cents": 10000,
        })
        self.assertEqual(res.net_cents, 40000)
        self.assertEqual(res.platform_fee_cents, 1190)
        self.assertAlmostEqual(res.effective_fee_bps, 297.5, places=2)

    def test_full_voucher_zero_net_settlement_regression(self) -> None:
        """
        Regression test for 100% promotional enterprise voucher where gross_cents == discount_cents.
        Must not raise ZeroDivisionError and must return effective_fee_bps == 0.0.
        """
        res = checkout_engine.process_settlement({
            "merchant_id": "merch_enterprise_promo",
            "customer_email": "cto@acme-corp.io",
            "currency": "USD",
            "gross_cents": 25000,
            "discount_cents": 25000,
        })
        self.assertEqual(res.net_cents, 0)
        self.assertEqual(res.platform_fee_cents, 0)
        self.assertEqual(res.effective_fee_bps, 0.0)

    def test_multi_currency_ngn_and_kes_exponent_regression(self) -> None:
        """
        Regression test for African multi-currency settlements (NGN, KES).
        Must not raise KeyError on DECIMAL_EXPONENTS.
        """
        res_ngn = checkout_engine.process_settlement({
            "merchant_id": "merch_lagos_hub",
            "customer_email": "rahmat@paystack.ng",
            "currency": "NGN",
            "gross_cents": 15000000,
            "discount_cents": 0,
        })
        self.assertEqual(res_ngn.currency, "NGN")
        self.assertGreater(res_ngn.usd_equivalent, 0.0)


if __name__ == "__main__":
    unittest.main()

