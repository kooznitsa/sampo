from django.test import tag, TestCase
from django.urls import reverse

from rest_framework import status

from authentication.tests.factories import DEFAULT_PASSWORD, UserFactory


@tag('admin', 'user_admin')
class TestUserAdmin(TestCase):

    def setUp(self) -> None:
        self.user = UserFactory.create()

    def test_enter_admin_with_correct_login_data(self) -> None:
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse('admin:index'), follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Администрирование сайта')

    def test_enter_admin_with_wrong_login_data(self) -> None:
        self.client.login(username='WrongUsername', password='WrongPassword')
        response = self.client.get(reverse('admin:index'), follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Войти')
