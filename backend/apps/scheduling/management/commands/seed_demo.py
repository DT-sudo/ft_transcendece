"""Populate a fresh database with demo positions, employees and a month of shifts."""

from __future__ import annotations

from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.scheduling.models import EmployeeUnavailability, Position, Shift, ShiftStatus
from apps.scheduling.services import assign_employees_to_shift

DEMO_PASSWORD = "demo12345!"
DEMO_ADMIN_EMAIL = "admin_demo@example.com"
DEMO_MANAGER_EMAIL = "manager_demo@example.com"
DEMO_EMPLOYEE_EMAIL = "employee_demo@example.com"
# The one-click demo login buttons, by role.
DEMO_ACCOUNTS = {"admin": DEMO_ADMIN_EMAIL, "manager": DEMO_MANAGER_EMAIL, "employee": DEMO_EMPLOYEE_EMAIL}

# (first name, last name, position). Positions are created from this list.
EMPLOYEES = [
    ("Demo", "Employee", "Barista"),
    ("Maya", "Rossi", "Barista"),
    ("Ivan", "Novak", "Barista"),
    ("Sofia", "Lang", "Bartender"),
    ("Tomas", "Weber", "Bartender"),
    ("Elena", "Cruz", "Waiter"),
    ("Jonas", "Meyer", "Waiter"),
    ("Nadia", "Fischer", "Head Chef"),
]

# One shift per position per day (Sundays closed): (position, start, end, capacity)
SHIFT_TEMPLATES = [
    ("Barista", time(7, 0), time(15, 0), 2),
    ("Head Chef", time(9, 0), time(17, 0), 1),
    ("Waiter", time(11, 0), time(19, 0), 2),
    ("Bartender", time(15, 0), time(23, 0), 2),
]


def _user(email: str, first: str, last: str, role: str, position: Position | None, password: str) -> User:
    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": first, "last_name": last, "role": role, "position": position},
    )
    if created:
        user.set_password(password)
        user.save(update_fields=["password"])
    return user


class Command(BaseCommand):
    help = "Populate the database with demo positions, employees and a month of shifts."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        _user(DEMO_ADMIN_EMAIL, "Demo", "Admin", UserRole.ADMIN, None, DEMO_PASSWORD)
        manager = _user(DEMO_MANAGER_EMAIL, "Demo", "Manager", UserRole.MANAGER, None, DEMO_PASSWORD)
        positions = {name: Position.objects.get_or_create(name=name)[0] for _, _, name in EMPLOYEES}

        pool: dict[str, list[User]] = {}
        for first, last, position in EMPLOYEES:
            email = DEMO_EMPLOYEE_EMAIL if first == "Demo" else f"{first.lower()}.{last.lower()}@example.com"
            password = DEMO_PASSWORD if first == "Demo" else User.generate_password()
            pool.setdefault(position, []).append(_user(email, first, last, UserRole.EMPLOYEE, positions[position], password))

        if Shift.objects.filter(created_by=manager).exists():
            self.stdout.write(self.style.WARNING("Demo shifts already present - skipping."))
            return

        today = timezone.localdate()
        start = today - timedelta(days=today.weekday() + 7)  # Monday of last week
        created = 0
        for offset in range(28):
            day = start + timedelta(days=offset)
            if day.weekday() == 6:
                continue
            for position, begin, finish, capacity in SHIFT_TEMPLATES:
                shift = Shift.objects.create(
                    date=day,
                    start_time=begin,
                    end_time=finish,
                    capacity=capacity,
                    position=positions[position],
                    created_by=manager,
                    # Past and current weeks are published; later weeks stay draft.
                    status=ShiftStatus.PUBLISHED if day < today + timedelta(days=7) else ShiftStatus.DRAFT,
                )
                # Rotate through the position's staff so nobody works every day.
                staff = pool[position]
                assign_employees_to_shift(shift, [staff[(offset + i) % len(staff)].id for i in range(min(capacity, len(staff)))])
                created += 1

        # A few upcoming days off, so the live-availability feature has something to show.
        for index, employee in enumerate([staff[0] for staff in pool.values()]):
            EmployeeUnavailability.objects.get_or_create(employee=employee, date=today + timedelta(days=9 + index * 2))

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(positions)} positions, {len(EMPLOYEES)} employees, {created} shifts."))
