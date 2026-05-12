from database.db import init_db, save_user, get_user_id_by_username
init_db()

save_user(999, "test_child")
child_id = get_user_id_by_username("test_child")

assert child_id == 999, "Username lookup failed"
print("All tests passed.")
