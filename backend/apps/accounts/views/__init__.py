"""
=============================================================================
ACCOUNTS VIEWS - MODULAR STRUCTURE
=============================================================================

HTTP view functions for the accounts app, split by concern so that work on
authentication and work on the employee directory touch different files:

├── __init__.py    - This file (exports all public views)
├── helpers.py     - Shared helpers (flash redirects, form error flattening)
├── auth.py        - Sign-up, login, logout, post-login routing
├── employees.py   - Manager-side employee CRUD and password reset

Import Pattern:
    from apps.accounts.views import login_view, manager_employees, ...

Or import the entire package:
    from apps.accounts import views
    views.login_view(request)

=============================================================================
"""

# Authentication
from .auth import (
    home,
    login_view,
    logout_view,
    signup_view,
)

# Manager-side employee directory
from .employees import (
    employee_delete,
    employee_update,
    manager_employees,
    manager_employees_create,
    reset_employee_password,
)

__all__ = [
    # Authentication
    "home",
    "login_view",
    "logout_view",
    "signup_view",
    # Employee directory
    "employee_delete",
    "employee_update",
    "manager_employees",
    "manager_employees_create",
    "reset_employee_password",
]
