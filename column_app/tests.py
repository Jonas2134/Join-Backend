from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from board_app.models import Board
from column_app.models import Column

User = get_user_model()


class ColumnTestSetUp(APITestCase):
    """Base class that creates a user, a board, and authenticates via JWT cookie."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.board = Board.objects.create(
            title="Test Board", owner=self.user
        )
        self.board.members.add(self.user)
        self.authenticate(self.user)

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)

    def create_column(self, name="Column", wip_limit=None):
        """Helper to create a column directly via the model."""
        return Column.objects.create(
            board=self.board, name=name, wip_limit=wip_limit
        )

    def get_list_url(self):
        return f"/api/boards/{self.board.pk}/columns/"

    def get_detail_url(self, column_pk):
        return f"/api/columns/{column_pk}/"


class ColumnCreationTests(ColumnTestSetUp):
    """Tests for column creation via the API and auto-position assignment."""

    def test_create_column_returns_201(self):
        response = self.client.post(self.get_list_url(), {"name": "To Do"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_column_auto_position_first(self):
        """First column on a board should get position 1."""
        self.client.post(self.get_list_url(), {"name": "To Do"})
        column = Column.objects.get(name="To Do", board=self.board)
        self.assertEqual(column.position, 1)

    def test_create_multiple_columns_sequential_positions(self):
        """Multiple columns should receive sequential positions."""
        self.client.post(self.get_list_url(), {"name": "To Do"})
        self.client.post(self.get_list_url(), {"name": "In Progress"})
        self.client.post(self.get_list_url(), {"name": "Done"})

        columns = Column.objects.filter(board=self.board).order_by("position")
        positions = list(columns.values_list("position", flat=True))
        self.assertEqual(positions, [1, 2, 3])
        names = list(columns.values_list("name", flat=True))
        self.assertEqual(names, ["To Do", "In Progress", "Done"])

    def test_create_column_with_wip_limit(self):
        """Column should be created with the given WIP limit."""
        response = self.client.post(
            self.get_list_url(), {"name": "WIP Column", "wip_limit": 3}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        column = Column.objects.get(name="WIP Column", board=self.board)
        self.assertEqual(column.wip_limit, 3)

    def test_create_column_without_wip_limit_defaults_to_none(self):
        """Column without explicit WIP limit should have wip_limit=None."""
        self.client.post(self.get_list_url(), {"name": "No Limit"})
        column = Column.objects.get(name="No Limit", board=self.board)
        self.assertIsNone(column.wip_limit)

    def test_list_columns_returns_ordered_by_position(self):
        """GET on the list endpoint should return columns ordered by position."""
        self.create_column("First")
        self.create_column("Second")
        self.create_column("Third")

        response = self.client.get(self.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [col["name"] for col in response.data]
        self.assertEqual(names, ["First", "Second", "Third"])


class ColumnPositionReorderingTests(ColumnTestSetUp):
    """Tests for moving columns to new positions via PATCH."""

    def setUp(self):
        super().setUp()
        self.col1 = self.create_column("Col 1")
        self.col2 = self.create_column("Col 2")
        self.col3 = self.create_column("Col 3")
        self.col4 = self.create_column("Col 4")

    def test_move_column_forward(self):
        """Move Col 1 (position 1) to position 3. Columns 2 and 3 shift down."""
        response = self.client.patch(
            self.get_detail_url(self.col1.pk),
            {"position": 3},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.col1.refresh_from_db()
        self.col2.refresh_from_db()
        self.col3.refresh_from_db()
        self.col4.refresh_from_db()

        self.assertEqual(self.col1.position, 3)
        self.assertEqual(self.col2.position, 1)
        self.assertEqual(self.col3.position, 2)
        self.assertEqual(self.col4.position, 4)

    def test_move_column_backward(self):
        """Move Col 3 (position 3) to position 1. Columns 1 and 2 shift up."""
        response = self.client.patch(
            self.get_detail_url(self.col3.pk),
            {"position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.col1.refresh_from_db()
        self.col2.refresh_from_db()
        self.col3.refresh_from_db()
        self.col4.refresh_from_db()

        self.assertEqual(self.col3.position, 1)
        self.assertEqual(self.col1.position, 2)
        self.assertEqual(self.col2.position, 3)
        self.assertEqual(self.col4.position, 4)

    def test_move_column_same_position_no_change(self):
        """Patching a column with its current position should not change anything."""
        response = self.client.patch(
            self.get_detail_url(self.col2.pk),
            {"position": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.col1.refresh_from_db()
        self.col2.refresh_from_db()
        self.col3.refresh_from_db()
        self.col4.refresh_from_db()

        self.assertEqual(self.col1.position, 1)
        self.assertEqual(self.col2.position, 2)
        self.assertEqual(self.col3.position, 3)
        self.assertEqual(self.col4.position, 4)

    def test_move_last_column_to_first(self):
        """Move Col 4 (position 4) to position 1. All others shift up."""
        response = self.client.patch(
            self.get_detail_url(self.col4.pk),
            {"position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.col1.refresh_from_db()
        self.col2.refresh_from_db()
        self.col3.refresh_from_db()
        self.col4.refresh_from_db()

        self.assertEqual(self.col4.position, 1)
        self.assertEqual(self.col1.position, 2)
        self.assertEqual(self.col2.position, 3)
        self.assertEqual(self.col3.position, 4)


class ColumnDeletionTests(ColumnTestSetUp):
    """Tests for column deletion and automatic position adjustment."""

    def setUp(self):
        super().setUp()
        self.col1 = self.create_column("Col 1")
        self.col2 = self.create_column("Col 2")
        self.col3 = self.create_column("Col 3")
        self.col4 = self.create_column("Col 4")

    def test_delete_column_returns_204(self):
        response = self.client.delete(self.get_detail_url(self.col2.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_middle_column_adjusts_positions(self):
        """Deleting Col 2 (position 2) should shift Col 3 and Col 4 down by 1."""
        self.client.delete(self.get_detail_url(self.col2.pk))

        self.col1.refresh_from_db()
        self.col3.refresh_from_db()
        self.col4.refresh_from_db()

        self.assertEqual(self.col1.position, 1)
        self.assertEqual(self.col3.position, 2)
        self.assertEqual(self.col4.position, 3)

    def test_delete_first_column_adjusts_positions(self):
        """Deleting the first column shifts all subsequent columns down by 1."""
        self.client.delete(self.get_detail_url(self.col1.pk))

        self.col2.refresh_from_db()
        self.col3.refresh_from_db()
        self.col4.refresh_from_db()

        self.assertEqual(self.col2.position, 1)
        self.assertEqual(self.col3.position, 2)
        self.assertEqual(self.col4.position, 3)

    def test_delete_last_column_does_not_affect_others(self):
        """Deleting the last column should not change positions of earlier columns."""
        self.client.delete(self.get_detail_url(self.col4.pk))

        self.col1.refresh_from_db()
        self.col2.refresh_from_db()
        self.col3.refresh_from_db()

        self.assertEqual(self.col1.position, 1)
        self.assertEqual(self.col2.position, 2)
        self.assertEqual(self.col3.position, 3)

    def test_delete_column_reduces_total_count(self):
        """After deletion, the total column count should decrease by 1."""
        self.assertEqual(Column.objects.filter(board=self.board).count(), 4)
        self.client.delete(self.get_detail_url(self.col3.pk))
        self.assertEqual(Column.objects.filter(board=self.board).count(), 3)


class ColumnPermissionTests(ColumnTestSetUp):
    """Tests for column access control (board membership, authentication)."""

    def test_unauthenticated_user_cannot_list_columns(self):
        """A request without an access token should be denied."""
        self.client.cookies.clear()
        response = self.client.get(self.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_member_cannot_list_columns(self):
        """A user who is not a board member or owner should be denied."""
        other_user = User.objects.create_user(
            username="other", password="otherpass123"
        )
        self.authenticate(other_user)
        response = self.client.get(self.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_member_cannot_create_column(self):
        """A non-member user cannot create a column on the board."""
        other_user = User.objects.create_user(
            username="other", password="otherpass123"
        )
        self.authenticate(other_user)
        response = self.client.post(self.get_list_url(), {"name": "Nope"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_member_can_create_column(self):
        """A board member (non-owner) should be able to create columns."""
        member = User.objects.create_user(
            username="member", password="memberpass123"
        )
        self.board.members.add(member)
        self.authenticate(member)
        response = self.client.post(self.get_list_url(), {"name": "Member Col"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
