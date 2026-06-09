"""browser-skill — drive the user's own browser as them.

Thin CLI client (`cli`) over an auto-managed background daemon (`daemon`) that
holds one Patchright `connect_over_cdp` session, the current page, and the
snapshot ref-map in memory.
"""

__version__ = "0.1.0"
