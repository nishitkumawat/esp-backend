from .auth import login_view, logout_view, forgot_password_view, verify_otp_view, reset_password_view, signup_view
from .dashboard import dashboard
from .inventory import (
    item_catalog, inventory_list, item_create, item_edit, item_detail, item_delete, add_stock, inventory_entry_delete,
    stock_move_view, completed_stock, stock_history, item_groups, process_wise_stock, assignee_wise_stock,
)
from .machines import machine_list, machine_create, machine_edit, machine_detail
from .dispatch import dispatch_list, dispatch_create, dispatch_detail
from .settings import settings_view, process_create_edit, process_delete, user_list, user_create_edit, assignee_create_edit, assignee_delete

__all__ = [
    'login_view', 'logout_view', 'forgot_password_view', 'verify_otp_view', 'reset_password_view', 'signup_view',
    'dashboard',
    'item_catalog', 'inventory_list', 'item_create', 'item_edit', 'item_detail', 'item_delete', 'add_stock', 'inventory_entry_delete', 'stock_move_view', 'completed_stock', 'stock_history', 'item_groups', 'process_wise_stock', 'assignee_wise_stock',
    'machine_list', 'machine_create', 'machine_edit', 'machine_detail',
    'dispatch_list', 'dispatch_create', 'dispatch_detail',
    'settings_view', 'process_create_edit', 'process_delete', 'user_list', 'user_create_edit', 'assignee_create_edit', 'assignee_delete',
]
