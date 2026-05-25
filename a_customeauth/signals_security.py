import django.dispatch

# Fired when an account gets locked out after too many failed attempts
account_locked = django.dispatch.Signal()

# Fired when a login from a new IP is detected for a user
new_ip_login = django.dispatch.Signal()

# Fired when admin session IP mismatch is detected
session_ip_mismatch = django.dispatch.Signal()

# Fired when a password is changed
password_changed = django.dispatch.Signal()

# Fired on successful login
user_logged_in_custom = django.dispatch.Signal()
