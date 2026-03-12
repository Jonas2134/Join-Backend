from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from board_app.models import Board
from column_app.models import Column
from task_app.models import Task

User = get_user_model()


class TaskTestSetUp(APITestCase):
    """Base class that creates a user, board, columns, and authenticates via JWT cookie."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.board = Board.objects.create(
            title="Test Board", owner=self.user
        )
        self.board.members.add(self.user)

        self.col_todo = Column.objects.create(
            board=self.board, name="To Do"
        )
        self.col_progress = Column.objects.create(
            board=self.board, name="In Progress"
        )
        self.col_done = Column.objects.create(
            board=self.board, name="Done"
        )

        self.authenticate(self.user)

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)

    def create_task(self, title="Task", column=None, assignee=None):
        """Helper to create a task directly via the model."""
        if column is None:
            column = self.col_todo
        return Task.objects.create(
            title=title, column=column, assignee=assignee
        )

    def get_list_url(self, column_pk):
        return f"/api/columns/{column_pk}/tasks/"

    def get_detail_url(self, task_pk):
        return f"/api/tasks/{task_pk}/"


class TaskCreationTests(TaskTestSetUp):
    """Tests for task creation via the API and auto-position assignment."""

    def test_create_task_returns_201(self):
        response = self.client.post(
            self.get_list_url(self.col_todo.pk),
            {"title": "My Task"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_task_auto_position_first(self):
        """First task in a column should get position 1."""
        self.client.post(
            self.get_list_url(self.col_todo.pk),
            {"title": "First Task"},
        )
        task = Task.objects.get(title="First Task")
        self.assertEqual(task.position, 1)

    def test_create_multiple_tasks_sequential_positions(self):
        """Multiple tasks in the same column should get sequential positions."""
        self.client.post(
            self.get_list_url(self.col_todo.pk), {"title": "Task 1"}
        )
        self.client.post(
            self.get_list_url(self.col_todo.pk), {"title": "Task 2"}
        )
        self.client.post(
            self.get_list_url(self.col_todo.pk), {"title": "Task 3"}
        )

        tasks = Task.objects.filter(column=self.col_todo).order_by("position")
        positions = list(tasks.values_list("position", flat=True))
        self.assertEqual(positions, [1, 2, 3])

    def test_create_task_with_valid_assignee(self):
        """A board member can be assigned to a task."""
        response = self.client.post(
            self.get_list_url(self.col_todo.pk),
            {"title": "Assigned Task", "assignee": self.user.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="Assigned Task")
        self.assertEqual(task.assignee, self.user)

    def test_create_task_with_non_member_assignee_fails(self):
        """Assigning a non-member user should return 400."""
        non_member = User.objects.create_user(
            username="outsider", password="outsiderpass123"
        )
        response = self.client.post(
            self.get_list_url(self.col_todo.pk),
            {"title": "Bad Task", "assignee": non_member.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_tasks_returns_ordered_by_position(self):
        """GET on the list endpoint should return tasks ordered by position."""
        self.create_task("First", self.col_todo)
        self.create_task("Second", self.col_todo)
        self.create_task("Third", self.col_todo)

        response = self.client.get(self.get_list_url(self.col_todo.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [t["title"] for t in response.data]
        self.assertEqual(titles, ["First", "Second", "Third"])


class TaskWipLimitTests(TaskTestSetUp):
    """Tests for WIP (Work In Progress) limit enforcement."""

    def setUp(self):
        super().setUp()
        self.wip_column = Column.objects.create(
            board=self.board, name="WIP Column", wip_limit=2
        )

    def test_create_task_under_wip_limit(self):
        """Creating a task when the column is under the WIP limit should succeed."""
        response = self.client.post(
            self.get_list_url(self.wip_column.pk),
            {"title": "Task 1"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_task_at_wip_limit_fails(self):
        """Creating a task when the column is at its WIP limit should return 400."""
        self.create_task("Task 1", self.wip_column)
        self.create_task("Task 2", self.wip_column)

        response = self.client.post(
            self.get_list_url(self.wip_column.pk),
            {"title": "Task 3"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_task_away_from_full_column(self):
        """Moving a task out of a full column should succeed."""
        task1 = self.create_task("Task 1", self.wip_column)
        self.create_task("Task 2", self.wip_column)

        response = self.client.patch(
            self.get_detail_url(task1.pk),
            {"column": self.col_todo.pk, "position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task1.refresh_from_db()
        self.assertEqual(task1.column, self.col_todo)

    def test_move_task_into_full_column_fails(self):
        """Moving a task into a column at its WIP limit should return 400."""
        self.create_task("Task 1", self.wip_column)
        self.create_task("Task 2", self.wip_column)
        outside_task = self.create_task("Outside Task", self.col_todo)

        response = self.client.patch(
            self.get_detail_url(outside_task.pk),
            {"column": self.wip_column.pk, "position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_task_within_full_column_same_column_succeeds(self):
        """Reordering within the same column should work even if WIP limit is reached."""
        task1 = self.create_task("Task 1", self.wip_column)
        task2 = self.create_task("Task 2", self.wip_column)

        response = self.client.patch(
            self.get_detail_url(task1.pk),
            {"position": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task1.refresh_from_db()
        task2.refresh_from_db()
        self.assertEqual(task1.position, 2)
        self.assertEqual(task2.position, 1)

    def test_column_without_wip_limit_allows_unlimited_tasks(self):
        """A column with no WIP limit should accept any number of tasks."""
        for i in range(10):
            response = self.client.post(
                self.get_list_url(self.col_todo.pk),
                {"title": f"Task {i}"},
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.filter(column=self.col_todo).count(), 10)


class TaskPositionReorderingTests(TaskTestSetUp):
    """Tests for reordering tasks within the same column via PATCH."""

    def setUp(self):
        super().setUp()
        self.task1 = self.create_task("Task 1", self.col_todo)
        self.task2 = self.create_task("Task 2", self.col_todo)
        self.task3 = self.create_task("Task 3", self.col_todo)
        self.task4 = self.create_task("Task 4", self.col_todo)

    def test_move_task_forward(self):
        """Move Task 1 (position 1) to position 3. Tasks 2 and 3 shift down."""
        response = self.client.patch(
            self.get_detail_url(self.task1.pk),
            {"position": 3},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.task3.refresh_from_db()
        self.task4.refresh_from_db()

        self.assertEqual(self.task1.position, 3)
        self.assertEqual(self.task2.position, 1)
        self.assertEqual(self.task3.position, 2)
        self.assertEqual(self.task4.position, 4)

    def test_move_task_backward(self):
        """Move Task 4 (position 4) to position 2. Tasks 2 and 3 shift up."""
        response = self.client.patch(
            self.get_detail_url(self.task4.pk),
            {"position": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.task3.refresh_from_db()
        self.task4.refresh_from_db()

        self.assertEqual(self.task1.position, 1)
        self.assertEqual(self.task4.position, 2)
        self.assertEqual(self.task2.position, 3)
        self.assertEqual(self.task3.position, 4)

    def test_move_task_same_position_no_change(self):
        """Patching a task with its current position should not change anything."""
        response = self.client.patch(
            self.get_detail_url(self.task2.pk),
            {"position": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.task3.refresh_from_db()
        self.task4.refresh_from_db()

        self.assertEqual(self.task1.position, 1)
        self.assertEqual(self.task2.position, 2)
        self.assertEqual(self.task3.position, 3)
        self.assertEqual(self.task4.position, 4)


class TaskColumnChangeTests(TaskTestSetUp):
    """Tests for moving tasks between columns."""

    def setUp(self):
        super().setUp()
        self.task1 = self.create_task("Task 1", self.col_todo)
        self.task2 = self.create_task("Task 2", self.col_todo)
        self.task3 = self.create_task("Task 3", self.col_todo)

    def test_move_task_to_different_column(self):
        """Moving a task to a different column should update its column."""
        response = self.client.patch(
            self.get_detail_url(self.task2.pk),
            {"column": self.col_progress.pk, "position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task2.refresh_from_db()
        self.assertEqual(self.task2.column, self.col_progress)
        self.assertEqual(self.task2.position, 1)

    def test_move_task_to_different_column_adjusts_old_column_positions(self):
        """After moving Task 2 out of col_todo, Task 3 should shift down."""
        self.client.patch(
            self.get_detail_url(self.task2.pk),
            {"column": self.col_progress.pk, "position": 1},
            format="json",
        )

        self.task1.refresh_from_db()
        self.task3.refresh_from_db()

        self.assertEqual(self.task1.position, 1)
        self.assertEqual(self.task3.position, 2)

    def test_move_task_into_column_with_existing_tasks(self):
        """Moving a task into a column that already has tasks should insert at given position."""
        existing = self.create_task("Existing", self.col_progress)

        response = self.client.patch(
            self.get_detail_url(self.task1.pk),
            {"column": self.col_progress.pk, "position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task1.refresh_from_db()
        existing.refresh_from_db()

        self.assertEqual(self.task1.column, self.col_progress)
        self.assertEqual(self.task1.position, 1)
        self.assertEqual(existing.position, 2)

    def test_cannot_move_task_to_column_in_different_board(self):
        """Moving a task to a column on a different board should return 400."""
        other_board = Board.objects.create(
            title="Other Board", owner=self.user
        )
        other_board.members.add(self.user)
        other_column = Column.objects.create(
            board=other_board, name="Other Column"
        )

        response = self.client.patch(
            self.get_detail_url(self.task1.pk),
            {"column": other_column.pk, "position": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskDeletionTests(TaskTestSetUp):
    """Tests for task deletion and automatic position adjustment."""

    def setUp(self):
        super().setUp()
        self.task1 = self.create_task("Task 1", self.col_todo)
        self.task2 = self.create_task("Task 2", self.col_todo)
        self.task3 = self.create_task("Task 3", self.col_todo)
        self.task4 = self.create_task("Task 4", self.col_todo)

    def test_delete_task_returns_204(self):
        response = self.client.delete(self.get_detail_url(self.task2.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_middle_task_adjusts_positions(self):
        """Deleting Task 2 (position 2) should shift Task 3 and Task 4 down."""
        self.client.delete(self.get_detail_url(self.task2.pk))

        self.task1.refresh_from_db()
        self.task3.refresh_from_db()
        self.task4.refresh_from_db()

        self.assertEqual(self.task1.position, 1)
        self.assertEqual(self.task3.position, 2)
        self.assertEqual(self.task4.position, 3)

    def test_delete_first_task_adjusts_positions(self):
        """Deleting the first task shifts all subsequent tasks down by 1."""
        self.client.delete(self.get_detail_url(self.task1.pk))

        self.task2.refresh_from_db()
        self.task3.refresh_from_db()
        self.task4.refresh_from_db()

        self.assertEqual(self.task2.position, 1)
        self.assertEqual(self.task3.position, 2)
        self.assertEqual(self.task4.position, 3)

    def test_delete_last_task_does_not_affect_others(self):
        """Deleting the last task should not change positions of earlier tasks."""
        self.client.delete(self.get_detail_url(self.task4.pk))

        self.task1.refresh_from_db()
        self.task2.refresh_from_db()
        self.task3.refresh_from_db()

        self.assertEqual(self.task1.position, 1)
        self.assertEqual(self.task2.position, 2)
        self.assertEqual(self.task3.position, 3)

    def test_delete_task_reduces_total_count(self):
        """After deletion, the total task count should decrease by 1."""
        self.assertEqual(Task.objects.filter(column=self.col_todo).count(), 4)
        self.client.delete(self.get_detail_url(self.task3.pk))
        self.assertEqual(Task.objects.filter(column=self.col_todo).count(), 3)


class TaskPermissionTests(TaskTestSetUp):
    """Tests for task access control."""

    def test_unauthenticated_user_cannot_list_tasks(self):
        """A request without an access token should be denied."""
        self.client.cookies.clear()
        response = self.client.get(self.get_list_url(self.col_todo.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_member_cannot_create_task(self):
        """A non-member user cannot create a task on the board."""
        non_member = User.objects.create_user(
            username="outsider", password="outsiderpass123"
        )
        self.authenticate(non_member)
        response = self.client.post(
            self.get_list_url(self.col_todo.pk),
            {"title": "Unauthorized Task"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_member_can_create_task(self):
        """A board member (non-owner) should be able to create tasks."""
        member = User.objects.create_user(
            username="member", password="memberpass123"
        )
        self.board.members.add(member)
        self.authenticate(member)
        response = self.client.post(
            self.get_list_url(self.col_todo.pk),
            {"title": "Member Task"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
