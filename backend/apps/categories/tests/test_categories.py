from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.common.test_utils import auth_client, create_user


class CategoryCrudTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="cat@example.com")
        self.client_a = auth_client(self.user)

    def test_create_category(self):
        response = self.client_a.post(reverse("category-list"), {"name": "Groceries"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Category.objects.filter(user=self.user, name="Groceries").exists())

    def test_list_categories_scoped_to_user(self):
        other = create_user(email="other-cat@example.com")
        Category.objects.create(user=self.user, name="Rent")
        Category.objects.create(user=other, name="Rent")

        response = self.client_a.get(reverse("category-list"))
        names = [row["name"] for row in response.data["results"]]
        self.assertEqual(names, ["Rent"])

    def test_duplicate_name_for_same_user_rejected(self):
        Category.objects.create(user=self.user, name="Dining")
        response = self.client_a.post(reverse("category-list"), {"name": "dining"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_name_allowed_for_different_users(self):
        other = create_user(email="other-cat2@example.com")
        Category.objects.create(user=other, name="Utilities")
        response = self.client_a.post(reverse("category-list"), {"name": "Utilities"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_update_category(self):
        category = Category.objects.create(user=self.user, name="Entertainment")
        response = self.client_a.patch(reverse("category-detail", args=[category.id]), {"name": "Fun"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.name, "Fun")

    def test_delete_category_without_transactions(self):
        category = Category.objects.create(user=self.user, name="Misc")
        response = self.client_a.delete(reverse("category-detail", args=[category.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=category.id).exists())


class CategoryIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="a-cat@example.com")
        self.user_b = create_user(email="b-cat@example.com")
        self.category_a = Category.objects.create(user=self.user_a, name="Salary")

    def test_user_cannot_retrieve_other_users_category(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("category-detail", args=[self.category_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_category(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("category-detail", args=[self.category_a.id]), {"name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.category_a.refresh_from_db()
        self.assertEqual(self.category_a.name, "Salary")

    def test_user_cannot_delete_other_users_category(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("category-detail", args=[self.category_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Category.objects.filter(id=self.category_a.id).exists())
