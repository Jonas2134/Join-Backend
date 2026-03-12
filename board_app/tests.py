from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from board_app.models import Board
from column_app.models import Column

User = get_user_model()


class BaseTestSetUp(APITestCase):
    """Base test class with common fixtures and authentication helper."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="ownerpass123"
        )
        self.member = User.objects.create_user(
            username="member", password="memberpass123"
        )
        self.stranger = User.objects.create_user(
            username="stranger", password="strangerpass123"
        )
        self.guest_user = User.objects.create_user(
            username="guest", password="guestpass123", is_guest=True
        )

        self.board = Board.objects.create(
            title="Test Board",
            description="A board for testing",
            owner=self.owner,
        )
        self.board.members.set([self.owner, self.member])

        self.archived_board = Board.objects.create(
            title="Archived Board",
            description="An archived board",
            owner=self.owner,
            is_active=False,
        )
        self.archived_board.members.set([self.owner, self.member])

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)


# ---------------------------------------------------------------------------
# 1. IsBoardOwner Tests (via Board API)
# ---------------------------------------------------------------------------
class IsBoardOwnerTests(BaseTestSetUp):
    """Tests that only the board owner can PATCH and DELETE a board."""

    def test_owner_can_patch_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.patch(url, {"title": "Updated Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, "Updated Title")

    def test_owner_can_delete_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())

    def test_member_cannot_patch_board(self):
        self.authenticate(self.member)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.patch(url, {"title": "Hacked Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, "Test Board")

    def test_member_cannot_delete_board(self):
        self.authenticate(self.member)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())

    def test_stranger_cannot_patch_board(self):
        self.authenticate(self.stranger)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.patch(url, {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stranger_cannot_delete_board(self):
        self.authenticate(self.stranger)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 2. IsBoardMemberOrOwner Tests (via Board API)
# ---------------------------------------------------------------------------
class IsBoardMemberOrOwnerTests(BaseTestSetUp):
    """Tests that board owners and members can GET, but strangers cannot."""

    def test_owner_can_get_board_detail(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Board")

    def test_member_can_get_board_detail(self):
        self.authenticate(self.member)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Board")

    def test_stranger_cannot_get_board_detail(self):
        self.authenticate(self.stranger)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_get_board_detail(self):
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 3. IsBoardActive Tests (via Column API)
# ---------------------------------------------------------------------------
class IsBoardActiveTests(BaseTestSetUp):
    """Tests that write operations are blocked on archived boards."""

    def setUp(self):
        super().setUp()
        self.active_column = Column.objects.create(
            board=self.board, name="To Do"
        )
        self.archived_column = Column.objects.create(
            board=self.archived_board, name="Archived Column"
        )

    def test_can_create_column_on_active_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/columns/"
        response = self.client.post(url, {"name": "In Progress"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Column.objects.filter(board=self.board, name="In Progress").exists()
        )

    def test_cannot_create_column_on_archived_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.archived_board.pk}/columns/"
        response = self.client.post(url, {"name": "New Column"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Column.objects.filter(board=self.archived_board, name="New Column").exists()
        )

    def test_can_get_columns_on_archived_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.archived_board.pk}/columns/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_patch_column_on_archived_board(self):
        self.authenticate(self.owner)
        url = f"/api/columns/{self.archived_column.pk}/"
        response = self.client.patch(url, {"name": "Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.archived_column.refresh_from_db()
        self.assertEqual(self.archived_column.name, "Archived Column")

    def test_cannot_delete_column_on_archived_board(self):
        self.authenticate(self.owner)
        url = f"/api/columns/{self.archived_column.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Column.objects.filter(pk=self.archived_column.pk).exists())

    def test_can_patch_column_on_active_board(self):
        self.authenticate(self.owner)
        url = f"/api/columns/{self.active_column.pk}/"
        response = self.client.patch(url, {"name": "Done"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_column.refresh_from_db()
        self.assertEqual(self.active_column.name, "Done")

    def test_can_delete_column_on_active_board(self):
        self.authenticate(self.owner)
        url = f"/api/columns/{self.active_column.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Column.objects.filter(pk=self.active_column.pk).exists())

    def test_member_can_get_columns_on_archived_board(self):
        self.authenticate(self.member)
        url = f"/api/boards/{self.archived_board.pk}/columns/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_cannot_create_column_on_archived_board(self):
        self.authenticate(self.member)
        url = f"/api/boards/{self.archived_board.pk}/columns/"
        response = self.client.post(url, {"name": "Blocked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 4. Board CRUD Tests
# ---------------------------------------------------------------------------
class BoardCRUDTests(BaseTestSetUp):
    """Tests for board list, create, detail, update, and delete operations."""

    def test_list_boards_shows_only_member_boards(self):
        self.authenticate(self.member)
        url = "/api/boards/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        board_ids = [b["id"] for b in response.data]
        self.assertIn(self.board.pk, board_ids)
        self.assertIn(self.archived_board.pk, board_ids)

    def test_list_boards_excludes_non_member_boards(self):
        self.authenticate(self.stranger)
        url = "/api/boards/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_board_user_becomes_member(self):
        self.authenticate(self.stranger)
        url = "/api/boards/"
        response = self.client.post(
            url, {"title": "New Board", "description": "Fresh board"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_board = Board.objects.get(title="New Board")
        self.assertEqual(new_board.owner, self.stranger)
        self.assertIn(self.stranger, new_board.members.all())

    def test_create_board_with_members(self):
        self.authenticate(self.owner)
        url = "/api/boards/"
        response = self.client.post(
            url,
            {
                "title": "Team Board",
                "description": "Board with members",
                "members": [self.member.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_board = Board.objects.get(title="Team Board")
        self.assertIn(self.owner, new_board.members.all())
        self.assertIn(self.member, new_board.members.all())

    def test_board_detail_includes_members_and_columns(self):
        Column.objects.create(board=self.board, name="To Do")
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("members", response.data)
        self.assertIn("columns", response.data)
        self.assertEqual(len(response.data["members"]), 2)
        self.assertEqual(len(response.data["columns"]), 1)

    def test_owner_can_update_board_members(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.patch(
            url,
            {"members": [self.owner.pk, self.member.pk, self.stranger.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.board.refresh_from_db()
        member_ids = set(self.board.members.values_list("id", flat=True))
        self.assertEqual(member_ids, {self.owner.pk, self.member.pk, self.stranger.pk})

    def test_owner_always_remains_member_after_update(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.patch(
            url,
            {"members": [self.member.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.board.refresh_from_db()
        self.assertIn(self.owner, self.board.members.all())

    def test_owner_can_delete_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())

    def test_non_owner_cannot_delete_board(self):
        self.authenticate(self.member)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())

    def test_guest_cannot_add_members_to_board(self):
        self.authenticate(self.guest_user)
        url = "/api/boards/"
        response = self.client.post(
            url,
            {
                "title": "Guest Board",
                "description": "A guest board",
                "members": [self.member.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_guest_can_create_board_without_members(self):
        self.authenticate(self.guest_user)
        url = "/api/boards/"
        response = self.client.post(
            url,
            {"title": "Guest Solo Board"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_board = Board.objects.get(title="Guest Solo Board")
        self.assertEqual(new_board.owner, self.guest_user)
        self.assertIn(self.guest_user, new_board.members.all())

    def test_guest_owner_cannot_modify_board_members(self):
        guest_board = Board.objects.create(
            title="Guest Owned Board", owner=self.guest_user
        )
        guest_board.members.set([self.guest_user])
        self.authenticate(self.guest_user)
        url = f"/api/boards/{guest_board.pk}/"
        response = self.client.patch(
            url,
            {"members": [self.guest_user.pk, self.member.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_list_boards(self):
        url = "/api/boards/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_board(self):
        url = "/api/boards/"
        response = self.client.post(url, {"title": "Nope"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_archive_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.board.pk}/"
        response = self.client.patch(url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.board.refresh_from_db()
        self.assertFalse(self.board.is_active)

    def test_owner_can_reactivate_board(self):
        self.authenticate(self.owner)
        url = f"/api/boards/{self.archived_board.pk}/"
        response = self.client.patch(url, {"is_active": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.archived_board.refresh_from_db()
        self.assertTrue(self.archived_board.is_active)
