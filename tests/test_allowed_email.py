import pytest
from fastapi.testclient import TestClient

from mathutrice.app import app, is_allowed_email

ACCEPTED = [
    "alice@epf.fr",
    "alice@epfedu.fr",
    "alice@EPF.FR",
    "Alice.Martin@Epf.Fr",
    "alice@EPFEDU.fr",
]

REFUSED = [
    # Suffix look-alikes: the case the issue was originally opened about.
    "attacker@notepf.fr",
    "x@myepf.fr",
    "alice@epf.fr.evil.com",
    "alice@sub.epf.fr",
    # Malformed addresses.
    "attacker@evil.com@epf.fr",
    "@epf.fr",
    "alice",
    # Other domains and empty values.
    "someone@gmail.com",
    "",
    None,
]


@pytest.mark.parametrize("email", ACCEPTED)
def test_accepts_epf_addresses_whatever_the_domain_case(email):
    assert is_allowed_email(email) is True


@pytest.mark.parametrize("email", REFUSED)
def test_refuses_lookalike_and_malformed_addresses(email):
    assert is_allowed_email(email) is False


@pytest.fixture(scope="module")
def client():
    with TestClient(app, follow_redirects=False) as client:
        yield client


@pytest.mark.parametrize("email", ["alice@epf.fr", "alice@EPF.FR", "Alice.Martin@Epf.Fr"])
def test_dev_login_signs_in_an_accepted_address(client, email):
    response = client.post("/dev/login", data={"email": email})

    assert response.status_code == 303


@pytest.mark.parametrize("email", ["attacker@notepf.fr", "attacker@evil.com@epf.fr", "@epf.fr"])
def test_dev_login_refuses_a_refused_address_with_403(client, email):
    response = client.post("/dev/login", data={"email": email})

    assert response.status_code == 403
    assert "Adresse EPF obligatoire" in response.text
