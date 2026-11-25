"""Pytest configuration for PayReceivio tests."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

import pytest
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def owner_user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="Test@12345",
        full_name="Test Owner",
    )


@pytest.fixture
def logged_in_client(client, owner_user):
    client.login(email="test@example.com", password="Test@12345")
    return client
