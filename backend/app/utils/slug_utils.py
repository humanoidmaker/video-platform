"""Slug generation utilities."""

import re
import secrets


def generate_slug(title: str) -> str:
    """Generate a URL-safe slug from a title with a random suffix."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug.strip("-")
    suffix = secrets.token_hex(4)
    return f"{slug}-{suffix}" if slug else suffix


def generate_tag_slug(name: str) -> str:
    """Generate a slug for a tag (no random suffix)."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")
