from __future__ import annotations

from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.debug_views import ensure_demo_accounts
from apps.accounts.models import User, UserRole
from apps.scheduling.models import Assignment, EmployeeUnavailability, Position, Shift, ShiftStatus
from apps.scheduling.services import assign_employees_to_shift

POSITIONS = ["Barista", "Bartender", "Waiter", "Head Chef"]

EMPLOYEES = [
    ("Maya", "Rossi", "Barista"),
    ("Ivan", "Novak", "Barista"),
    ("Sofia", "Lang", "Bartender"),
    ("Tomas", "Weber", "Bartender"),
    ("Elena", "Cruz", "Waiter"),
    ("Jonas", "Meyer", "Waiter"),
    ("Nadia", "Fischer", "Head Chef"),
]

# (position, start, end, capacity)
SHIFT_TEMPLATES = [
    ("Barista", time(7, 0), time(15, 0), 2),
    ("Head Chef", time(9, 0), time(17, 0), 1),
    ("Waiter", time(11, 0), time(19, 0), 2),
    ("Bartender", time(15, 0), time(23, 0), 2),
]


class Command(BaseCommand):
    help = "Populate the database with demo positions, employees and a month of shifts."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo shifts before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        manager, demo_employee = ensure_demo_accounts()

        positions = {name: Position.objects.get_or_create(name=name)[0] for name in POSITIONS}
        demo_employee.position = positions["Barista"]
        demo_employee.save(update_fields=["position"])

        if options["reset"]:
            deleted, _ = Shift.objects.filter(created_by=manager).delete()
            self.stdout.write(f"Removed {deleted} existing shift rows.")

        if Shift.objects.filter(created_by=manager).exists():
            self.stdout.write(self.style.WARNING("Demo shifts already present - skipping. Use --reset to rebuild."))
            return

        employees = self._create_employees(positions)
        # The demo employee shares the Barista pool so the demo login has real shifts.
        employees.setdefault("Barista", []).insert(0, demo_employee)

        created, assigned = self._create_shifts(manager, positions, employees)
        self._create_unavailability(employees)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(POSITIONS)} positions, {sum(len(v) for v in employees.values())} employees, "
                f"{created} shifts ({assigned} assignments)."
            )
        )

    def _create_employees(self, positions: dict[str, Position]) -> dict[str, list[User]]:
        pool: dict[str, list[User]] = {}
        for first, last, position_name in EMPLOYEES:
            username = f"{first.lower()}.{last.lower()}@example.com"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": username,
                    "first_name": first,
                    "last_name": last,
                    "role": UserRole.EMPLOYEE,
                    "position": positions[position_name],
                    "is_active": True,
                },
            )
            if created:
                user.set_password(User.generate_password())
                user.save(update_fields=["password"])
            pool.setdefault(position_name, []).append(user)
        return pool

    def _create_shifts(
        self,
        manager: User,
        positions: dict[str, Position],
        employees: dict[str, list[User]],
    ) -> tuple[int, int]:
        today = timezone.localdate()
        start = today - timedelta(days=today.weekday() + 7)  # start of last week
        created = 0
        assigned = 0
        rotation: dict[str, int] = {name: 0 for name in POSITIONS}

        for offset in range(28):
            day = start + timedelta(days=offset)
            if day.weekday() == 6:  # closed on Sundays
                continue

            for position_name, begin, finish, capacity in SHIFT_TEMPLATES:
                # Keep the schedule uneven so the calendar looks like a real rota.
                if position_name == "Head Chef" and day.weekday() in (0, 1):
                    continue

                shift = Shift.objects.create(
                    date=day,
                    start_time=begin,
                    end_time=finish,
                    capacity=capacity,
                    position=positions[position_name],
                    created_by=manager,
                    # Past and current weeks are published; the upcoming week stays draft.
                    status=ShiftStatus.PUBLISHED if day < today + timedelta(days=7) else ShiftStatus.DRAFT,
                )
                created += 1

                pool = employees.get(position_name, [])
                if not pool:
                    continue
                picked = []
                for _ in range(min(capacity, len(pool))):
                    picked.append(pool[rotation[position_name] % len(pool)])
                    rotation[position_name] += 1
                picked = list(dict.fromkeys(picked))

                try:
                    assign_employees_to_shift(shift, [e.id for e in picked])
                    assigned += len(picked)
                except Exception:
                    # A rotation collision just leaves the shift understaffed, which is a valid state.
                    Assignment.objects.filter(shift=shift).delete()

        return created, assigned

    def _create_unavailability(self, employees: dict[str, list[User]]) -> None:
        today = timezone.localdate()
        flat = [e for pool in employees.values() for e in pool]
        for index, employee in enumerate(flat[:4]):
            day = today + timedelta(days=9 + index * 2)
            EmployeeUnavailability.objects.get_or_create(employee=employee, date=day)
