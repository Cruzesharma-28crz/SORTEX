import hashlib
from sortex_edge.client import digest

def test_digest_matches_sha256(tmp_path):
    path = tmp_path / "bundle.zip"
    path.write_bytes(b"sortex")
    assert digest(path) == hashlib.sha256(b"sortex").hexdigest()
