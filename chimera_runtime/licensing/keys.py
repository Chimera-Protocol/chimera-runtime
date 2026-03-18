"""
Embedded Ed25519 public key for license verification.

This is the PUBLIC key only -- it can verify signatures but never create them.
The corresponding PRIVATE key exists only on the Chimera dashboard server.
Rotate by updating this file and releasing a new package version.
"""

CHIMERA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAnJfHgnDYYY+FG9MyZlCuLbPMQ+AZWJ9BpJ4uAanjoa4=
-----END PUBLIC KEY-----"""
