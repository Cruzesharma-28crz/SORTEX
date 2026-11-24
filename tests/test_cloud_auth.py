from sortex_cloud.auth import Principal

def test_principal_contains_scoped_identity():
    principal = Principal(owner="friend-1", role="contributor")
    assert principal.owner == "friend-1"
    assert principal.role == "contributor"
