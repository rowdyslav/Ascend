"""Application-wide logging for the ASCEND frontend (stdlib only)."""

import logging

logger = logging.getLogger("ascend.frontend")

if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
