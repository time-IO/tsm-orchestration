#!/usr/bin/env python3

import sys
import requests

# Keycloak settings
host = "docker"
realm = "timeio"
admin_user = "keycloak"
admin_password = "keycloak"

test_username = "testuser"
test_password = "changeMe123!"
test_email = "testusere2e@example.de"
group_path = "/a:a:a:group:VO:Group1#"
client_id = "timeIO-client"


def get_admin_token():
    url = f"http://{host}/keycloak/realms/master/protocol/openid-connect/token"
    response = requests.post(
        url,
        data={
            "client_id": "admin-cli",
            "username": admin_user,
            "password": admin_password,
            "grant_type": "password",
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_user(token):
    url = f"http://{host}/keycloak/admin/realms/{realm}/users"
    payload = {
        "username": test_username,
        "email": test_email,
        "emailVerified": True,
        "firstName": "Test",
        "lastName": "User",
        "enabled": True,
        "credentials": [
            {
                "userLabel": "Password",
                "temporary": False,
                "type": "password",
                "value": test_password,
            }
        ],
        "requiredActions": [],
    }
    response = requests.post(
        url, headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    if response.status_code == 409:
        print(f"User {test_username} already exists, updating instead")
        user_id = get_user_id(token)
        update_response = requests.put(
            f"{url}/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        update_response.raise_for_status()
        return
    response.raise_for_status()
    print(f"Created user: {test_username}")


def get_user_id(token):
    url = f"http://{host}/keycloak/admin/realms/{realm}/users"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"username": test_username, "exact": "true"},
    )
    response.raise_for_status()
    users = response.json()
    if not users:
        print(f"User {test_username} not found")
        sys.exit(1)
    return users[0]["id"]


def create_or_get_group(token):
    url = f"http://{host}/keycloak/admin/realms/{realm}/groups"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"name": group_path.strip("/")},
    )
    if response.status_code not in (201, 409, 400):
        response.raise_for_status()

    # Look up the group id regardless of whether it was just created or already existed
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    for group in response.json():
        if group["path"] == group_path:
            return group["id"]
    print(f"Group {group_path} could not created or found")
    sys.exit(1)


def add_user_to_group(token, user_id, group_id):
    url = (
        f"http://{host}/keycloak/admin/realms/{realm}/users/{user_id}/groups/{group_id}"
    )
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    print(f"Added user {test_username} to group {group_path}")


def enable_direct_access_grants(token):
    url = f"http://{host}/keycloak/admin/realms/{realm}/clients"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"clientId": client_id},
    )
    response.raise_for_status()
    clients = response.json()
    if not clients:
        print(f"Client {client_id} not found")
        sys.exit(1)
    client_uuid = clients[0]["id"]

    if clients[0].get("directAccessGrantsEnabled"):
        print(f"Direct access grants enabled for {client_id}")
        return

    update_url = f"http://{host}/keycloak/admin/realms/{realm}/clients/{client_uuid}"
    client_data = clients[0]
    client_data["directAccessGrantsEnabled"] = True
    update_response = requests.put(
        update_url, headers={"Authorization": f"Bearer {token}"}, json=client_data
    )
    update_response.raise_for_status()
    print(f"Enabled direct access grants for {client_id}")


if __name__ == "__main__":
    token = get_admin_token()
    create_user(token)
    user_id = get_user_id(token)
    group_id = create_or_get_group(token)
    add_user_to_group(token, user_id, group_id)
    enable_direct_access_grants(token)
    print("Success!")
    sys.exit(0)
