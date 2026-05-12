import asyncio
from database.db import init_db, add_user_role, link_parent_child, get_user_roles, get_children

def test_db():
    init_db()
    # Mock user registration
    user_id = 123
    add_user_role(user_id, "Ученик")
    roles = get_user_roles(user_id)
    assert roles == ["Ученик"], f"Expected ['Ученик'], got {roles}"
    print("User roles test passed")

    parent_id = 456
    add_user_role(parent_id, "Родитель")
    link_parent_child(parent_id, user_id)
    children = get_children(parent_id)
    assert children == [user_id], f"Expected [{user_id}], got {children}"
    print("Parent-child link test passed")

test_db()
