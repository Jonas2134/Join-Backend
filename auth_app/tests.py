from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterViewTests(APITestCase):
    """Tests for the RegisterView endpoint."""

    URL = reverse('register')

    def test_successful_registration(self):
        """A valid registration creates a user and returns 201."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Str0ngP@ss99',
            'repeated_password': 'Str0ngP@ss99',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'User created successfully!')
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_guest)
        self.assertTrue(user.check_password('Str0ngP@ss99'))

    def test_registration_duplicate_username(self):
        """Registration with an existing username returns 400."""
        User.objects.create_user(username='taken', email='a@b.com', password='Str0ngP@ss99')
        data = {
            'username': 'taken',
            'email': 'other@example.com',
            'password': 'Str0ngP@ss99',
            'repeated_password': 'Str0ngP@ss99',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_registration_duplicate_email(self):
        """Registration with an existing email returns 400."""
        User.objects.create_user(username='existing', email='taken@example.com', password='Str0ngP@ss99')
        data = {
            'username': 'brandnew',
            'email': 'taken@example.com',
            'password': 'Str0ngP@ss99',
            'repeated_password': 'Str0ngP@ss99',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_mismatching_passwords(self):
        """Registration with non-matching passwords returns 400."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Str0ngP@ss99',
            'repeated_password': 'Different123!',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_password', response.data)

    def test_registration_weak_password_too_short(self):
        """Registration with a too-short password is rejected by validate_password."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Ab1!',
            'repeated_password': 'Ab1!',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_weak_password_too_common(self):
        """Registration with a common password is rejected by validate_password."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'repeated_password': 'password123',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_weak_password_entirely_numeric(self):
        """Registration with a purely numeric password is rejected by validate_password."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': '93847561029384',
            'repeated_password': '93847561029384',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class LoginViewTests(APITestCase):
    """Tests for the LoginView endpoint."""

    URL = reverse('login')

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Str0ngP@ss99',
        )

    def test_successful_login_sets_cookies(self):
        """Successful login returns 200 and sets access_token and refresh_token cookies."""
        data = {'username': 'testuser', 'password': 'Str0ngP@ss99'}
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertTrue(refresh_cookie['httponly'])

    def test_successful_login_response_body(self):
        """Login response body contains only the detail message."""
        data = {'username': 'testuser', 'password': 'Str0ngP@ss99'}
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Login successfully!'})
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_login_wrong_password(self):
        """Login with the wrong password returns 400."""
        data = {'username': 'testuser', 'password': 'WrongPassword1!'}
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Login with a non-existent username returns 400."""
        data = {'username': 'ghost', 'password': 'Str0ngP@ss99'}
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):
    """Tests for the LogoutView endpoint."""

    URL = reverse('logout')

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Str0ngP@ss99',
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access = self.refresh.access_token

    def test_successful_logout_blacklists_token_and_deletes_cookies(self):
        """Logout blacklists the refresh token and instructs cookie deletion."""
        self.client.cookies['access_token'] = str(self.access)
        self.client.cookies['refresh_token'] = str(self.refresh)
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Log-Out successfully!')
        # Cookies are set with empty value and max-age=0 to delete them
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')
        # Verify the refresh token is blacklisted by trying to use it
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        from rest_framework_simplejwt.exceptions import TokenError
        with self.assertRaises(TokenError):
            RT(str(self.refresh)).check_blacklist()

    def test_logout_guest_user_is_deleted(self):
        """Logging out a guest user deletes the guest user from the database."""
        guest = User.objects.create(username='guest_abc123', is_guest=True)
        guest.set_unusable_password()
        guest.save()
        guest_refresh = RefreshToken.for_user(guest)
        guest_access = guest_refresh.access_token
        self.client.cookies['access_token'] = str(guest_access)
        self.client.cookies['refresh_token'] = str(guest_refresh)
        guest_id = guest.id
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(id=guest_id).exists())

    def test_logout_without_refresh_token(self):
        """Logout without a refresh_token cookie returns 400."""
        self.client.cookies['access_token'] = str(self.access)
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Refresh token not found.')

    def test_logout_unauthenticated(self):
        """Logout without any authentication returns 401."""
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CookieTokenRefreshViewTests(APITestCase):
    """Tests for the CookieTokenRefreshView endpoint."""

    URL = reverse('token-refresh')

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Str0ngP@ss99',
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_successful_token_refresh(self):
        """Refresh with a valid refresh_token cookie returns 200 and sets new cookies."""
        self.client.cookies['refresh_token'] = str(self.refresh)
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['access'], 'Access Token refreshed successfully.')
        self.assertIn('access_token', response.cookies)
        # ROTATE_REFRESH_TOKENS is True, so a new refresh token is issued
        self.assertIn('refresh_token', response.cookies)

    def test_refresh_with_missing_cookie(self):
        """Refresh without the refresh_token cookie returns 401."""
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Refresh token not found.')

    def test_refresh_with_invalid_token(self):
        """Refresh with an invalid token returns 401."""
        self.client.cookies['refresh_token'] = 'invalid-garbage-token'
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid refresh token.')

    def test_refresh_with_blacklisted_token(self):
        """Refresh with an already-blacklisted token returns 401."""
        self.client.cookies['refresh_token'] = str(self.refresh)
        # Blacklist the token manually
        self.refresh.blacklist()
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GuestLoginViewTests(APITestCase):
    """Tests for the GuestLoginView endpoint."""

    URL = reverse('guest-login')

    def test_guest_login_creates_guest_user(self):
        """Guest login creates a user with is_guest=True."""
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Guest Login successfully!')
        guest_id = response.data['user']['id']
        guest = User.objects.get(id=guest_id)
        self.assertTrue(guest.is_guest)
        self.assertFalse(guest.has_usable_password())

    def test_guest_login_username_starts_with_guest_prefix(self):
        """Guest user username starts with 'guest_'."""
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        username = response.data['user']['username']
        self.assertTrue(username.startswith('guest_'))

    def test_guest_login_sets_cookies(self):
        """Guest login sets access_token and refresh_token cookies."""
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertTrue(refresh_cookie['httponly'])

    def test_guest_login_response_contains_user_data(self):
        """Guest login response contains user id, username, and is_guest flag."""
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['user']
        self.assertIn('id', user_data)
        self.assertIn('username', user_data)
        self.assertIn('is_guest', user_data)
        self.assertTrue(user_data['is_guest'])


class AuthStatusViewTests(APITestCase):
    """Tests for the AuthStatusView endpoint."""

    URL = reverse('auth-status')

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Str0ngP@ss99',
        )

    def test_returns_user_data_when_authenticated(self):
        """Authenticated request returns user data with 200."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access_token'] = str(refresh.access_token)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_authenticated'])
        user_data = response.data['user']
        self.assertEqual(user_data['id'], self.user.id)
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertFalse(user_data['is_guest'])

    def test_returns_401_when_not_authenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_guest_flag_for_guest_user(self):
        """Authenticated guest user is correctly indicated with is_guest=True."""
        guest = User.objects.create(username='guest_test01', is_guest=True)
        guest.set_unusable_password()
        guest.save()
        refresh = RefreshToken.for_user(guest)
        self.client.cookies['access_token'] = str(refresh.access_token)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['user']['is_guest'])


class PasswordChangeViewTests(APITestCase):
    """Tests for the PasswordChangeView endpoint."""

    URL = reverse('password-change')

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Str0ngP@ss99',
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access_token'] = str(refresh.access_token)

    def test_successful_password_change(self):
        """Valid password change returns 200 and updates the password."""
        data = {
            'old_password': 'Str0ngP@ss99',
            'new_password': 'NewStr0ng!Pass77',
            'repeated_new_password': 'NewStr0ng!Pass77',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Password changed successfully.')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStr0ng!Pass77'))

    def test_wrong_old_password(self):
        """Providing the wrong old password returns 400."""
        data = {
            'old_password': 'WrongOldPass1!',
            'new_password': 'NewStr0ng!Pass77',
            'repeated_new_password': 'NewStr0ng!Pass77',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_mismatching_new_passwords(self):
        """Mismatching new passwords return 400."""
        data = {
            'old_password': 'Str0ngP@ss99',
            'new_password': 'NewStr0ng!Pass77',
            'repeated_new_password': 'Completely!Different1',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_new_password', response.data)

    def test_weak_new_password_rejected(self):
        """A weak new password is rejected by validate_password."""
        data = {
            'old_password': 'Str0ngP@ss99',
            'new_password': '123',
            'repeated_new_password': '123',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_unauthenticated_request(self):
        """Password change without authentication returns 401."""
        self.client.cookies.clear()
        data = {
            'old_password': 'Str0ngP@ss99',
            'new_password': 'NewStr0ng!Pass77',
            'repeated_new_password': 'NewStr0ng!Pass77',
        }
        response = self.client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotGuestPermissionTests(APITestCase):
    """Tests for the NotGuest permission class."""

    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='Str0ngP@ss99',
            is_guest=False,
        )
        self.guest_user = User.objects.create(
            username='guest_perm01',
            is_guest=True,
        )
        self.guest_user.set_unusable_password()
        self.guest_user.save()

    def test_non_guest_user_passes(self):
        """NotGuest allows authenticated non-guest users."""
        from auth_app.api.permissions import NotGuest
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.regular_user
        permission = NotGuest()
        self.assertTrue(permission.has_permission(request, None))

    def test_guest_user_is_denied(self):
        """NotGuest denies authenticated guest users."""
        from auth_app.api.permissions import NotGuest
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.guest_user
        permission = NotGuest()
        self.assertFalse(permission.has_permission(request, None))

    def test_anonymous_user_passes(self):
        """NotGuest allows anonymous users (permission only blocks guests)."""
        from auth_app.api.permissions import NotGuest
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth.models import AnonymousUser

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        permission = NotGuest()
        self.assertTrue(permission.has_permission(request, None))
