from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.common.test_utils import auth_client, create_user
from apps.transactions.models import Transaction


class TransactionCrudTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="t@example.com")
        self.client_a = auth_client(self.user)
        self.category = Category.objects.create(user=self.user, name="Groceries")

    def test_create_transaction(self):
        response = self.client_a.post(reverse("transaction-list"), {
            "category": self.category.id, "transaction_type": "expense",
            "amount": "42.50", "description": "Weekly shop", "transaction_date": "2026-11-05",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Transaction.objects.filter(user=self.user, description="Weekly shop").exists())

    def test_negative_amount_rejected(self):
        response = self.client_a.post(reverse("transaction-list"), {
            "category": self.category.id, "transaction_type": "expense",
            "amount": "-5.00", "transaction_date": "2026-11-05",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_amount_rejected(self):
        response = self.client_a.post(reverse("transaction-list"), {
            "category": self.category.id, "transaction_type": "expense",
            "amount": "0.00", "transaction_date": "2026-11-05",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_transaction(self):
        txn = Transaction.objects.create(
            user=self.user, category=self.category, transaction_type="expense",
            amount="10.00", transaction_date="2026-11-01",
        )
        response = self.client_a.patch(reverse("transaction-detail", args=[txn.id]), {"amount": "15.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        txn.refresh_from_db()
        self.assertEqual(str(txn.amount), "15.00")

    def test_delete_transaction(self):
        txn = Transaction.objects.create(
            user=self.user, category=self.category, transaction_type="expense",
            amount="10.00", transaction_date="2026-11-01",
        )
        response = self.client_a.delete(reverse("transaction-detail", args=[txn.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(id=txn.id).exists())

    def test_filter_by_month(self):
        Transaction.objects.create(user=self.user, category=self.category, transaction_type="expense", amount="20.00", transaction_date="2026-11-05")
        Transaction.objects.create(user=self.user, category=self.category, transaction_type="expense", amount="30.00", transaction_date="2026-10-05")
        response = self.client_a.get(reverse("transaction-list"), {"month": "2026-11"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_transaction_type(self):
        Transaction.objects.create(user=self.user, category=self.category, transaction_type="expense", amount="20.00", transaction_date="2026-11-05")
        Transaction.objects.create(user=self.user, category=self.category, transaction_type="income", amount="1000.00", transaction_date="2026-11-01")
        response = self.client_a.get(reverse("transaction-list"), {"transaction_type": "income"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["transaction_type"], "income")


class TransactionIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.category_a = Category.objects.create(user=self.user_a, name="Groceries")
        self.txn_a = Transaction.objects.create(
            user=self.user_a, category=self.category_a, amount="50.00",
            transaction_type=Transaction.Type.EXPENSE, transaction_date="2026-01-15",
        )

    def test_user_cannot_list_other_users_transactions(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("transaction-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.txn_a.id, ids)

    def test_user_cannot_retrieve_other_users_transaction_by_id(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("transaction-detail", args=[self.txn_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_transaction_by_id(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("transaction-detail", args=[self.txn_a.id]), {"amount": "999.00"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.txn_a.refresh_from_db()
        self.assertEqual(str(self.txn_a.amount), "50.00")

    def test_user_cannot_delete_other_users_transaction_by_id(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("transaction-detail", args=[self.txn_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Transaction.objects.filter(pk=self.txn_a.id).exists())

    def test_user_cannot_create_transaction_against_other_users_category(self):
        client = auth_client(self.user_b)
        response = client.post(reverse("transaction-list"), {
            "category": self.category_a.id, "amount": "10.00",
            "transaction_type": "expense", "transaction_date": "2026-01-16",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
