import pytest
from www.core import WWWEnv, Synapse


def test_client():
    assert Synapse.client() is not None
    profile = Synapse.client().getUserProfile(refresh=True)
    assert profile['userName'] == WWWEnv.SYNAPSE_USERNAME()
