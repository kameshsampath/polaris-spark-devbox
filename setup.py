#!/usr/bin/env python
import json
import os
import re
from datetime import datetime
from pathlib import Path

import docker
import requests
from docker.models.containers import Container
from dotenv import load_dotenv

from log.logger import get_logger as logger

# Load .env file
load_dotenv()

LOGGER = logger("connection_config")
CLIENT = docker.from_env()


def get_polaris_container(
    project_name=os.getenv("COMPOSE_PROJECT_NAME"),
) -> Container:
    filters = {
        "label": ["com.docker.compose.project"],
        "name": ["polaris"],
        "status": "running",
    }
    if project_name:
        filters["label"].append(f"com.docker.compose.project={project_name}")

    containers = CLIENT.containers.list(all=True, filters=filters)
    if containers:
        return containers[0]
    return None


def extract_timestamp(line):
    # Extract timestamp part (first 30 characters) and convert to datetime
    timestamp_str = line[:26] + "Z"  # Truncate nanoseconds to microseconds
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        LOGGER.error(f"Error parsing timestamp from line: {line}")
        return datetime.min  # Return minimum date for invalid timestamps


def get_root_cred_log_lines() -> list[str]:
    polaris_container = get_polaris_container()
    if polaris_container:
        LOGGER.debug(f"Polaris Container with ID: {polaris_container.id}")
        logs = polaris_container.logs(timestamps=True).decode("utf-8")
        log_lines = logs.split("\n")
        line_with_root_creds = []
        for line in log_lines:
            if "root principal credentials" in line.lower():
                line_with_root_creds.append(line)
        return sorted(line_with_root_creds, key=extract_timestamp, reverse=True)
    return None


def extract_root_principal_credentials() -> tuple[str, str]:
    r_lines = get_root_cred_log_lines()
    cred_line = r_lines[0]
    if "root principal credentials" in cred_line.lower():
        match = re.search(
            r"root principal credentials\s*:(.*?)(?:\n|$)", cred_line, re.IGNORECASE
        )
        if match:
            return tuple(match.group(1).strip().split(":", 1))
    return None


def get_api_port(container_port: int = 8181):
    polaris_container = get_polaris_container()
    if polaris_container:
        # Format port string correctly (e.g., "8181/tcp")
        container_port = f"{container_port}/tcp"
        ports = polaris_container.attrs["NetworkSettings"]["Ports"]
        mappings = ports.get(container_port, [])

        return mappings[0]["HostPort"] if mappings else None

    return None


def get_auth_token(
    client_id: str,
    client_secret: str,
    polaris_api_host: str,
    polaris_api_port: int,
) -> str:
    headers = {
        "Authorization": f"Bearer {client_id}:{client_secret}",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        f"http://{polaris_api_host}:{polaris_api_port}/api/catalog/v1/oauth/tokens",
        headers=headers,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "PRINCIPAL_ROLE:ALL",
        },
    )
    if response.status_code == 200:
        return response.json()["access_token"]


def build_headers(
    auth_token: str,
    content_type: str = "application/json",
    accept: str = "application/json",
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {auth_token}",
        "accept": accept,
        "content-type": content_type,
    }


# Create the Catalog
def create_catalog(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    catalog_name: str = os.getenv("POLARIS_CATALOG_NAME", "my_catalog"),
    default_base_location: str = os.getenv(
        "POLARIS_DEFAULT_BASE_LOCATION", "file:///data/polaris"
    ),
    storage_type="FILE",
    allowed_locations=[],
):
    if not allowed_locations:
        allowed_locations.append(default_base_location)

    payload = {
        "catalog": {
            "name": catalog_name,
            "type": "INTERNAL",
            "readOnly": False,
            "properties": {"default-base-location": default_base_location},
            "storageConfigInfo": {
                "storageType": storage_type,
                "allowedLocations": allowed_locations,
            },
        }
    }
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.post(
            f"{polaris_catalog_mgmt_uri}/catalogs",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info("Catalog Created Successfully")
            if response.content:
                LOGGER.debug("Response:", response.json())

    except requests.exceptions.RequestException as e:
        print(response.json())
        print(f"An error occurred: {e}")


def create_principal(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    principal_name: str = os.getenv("POLARIS_PRINCIPAL_NAME", "polarisuser"),
    type: str = "user",
) -> tuple[str, str]:
    payload = {
        "name": principal_name,
        "type": type,
    }
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.post(
            f"{polaris_catalog_mgmt_uri}/principals",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info(f"Principal {principal_name} Created Successfully")
            if response.content:
                r_json = response.json()
                LOGGER.debug(r_json)
                principal_creds = r_json["credentials"]
                LOGGER.debug(f"Credentials {principal_creds}")
                return (
                    principal_creds["clientId"],
                    principal_creds["clientSecret"],
                )

    except requests.exceptions.RequestException as e:
        print(response.json())
        print(f"An error occurred: {e}")

    return None


def create_principal_role(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    role_name: str = os.getenv("POLARIS_PRINCIPAL_ROLE_NAME", "polarisuser_role"),
):
    payload = {"name": role_name}
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.post(
            f"{polaris_catalog_mgmt_uri}/principal-roles",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info(f"Principal Role {role_name} Created Successfully")

    except requests.exceptions.RequestException as e:
        print(response.json())
        print(f"An error occurred: {e}")


def assign_role_to_principal(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    role_name: str = os.getenv("POLARIS_PRINCIPAL_ROLE_NAME", "polarisuser_role"),
    principal_name: str = os.getenv("POLARIS_PRINCIPAL_NAME", "polarisuser"),
):
    payload = {
        "principalRole": {"name": role_name},
    }
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.put(
            f"{polaris_catalog_mgmt_uri}/principals/{principal_name}/principal-roles",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info(f"Principal Role '{role_name}' assigned to '{principal_name}'")

    except requests.exceptions.RequestException as e:
        print(response.json())
        print(f"An error occurred: {e}")


def create_catalog_role(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    catalog_name: str = os.getenv("POLARIS_CATALOG_NAME", "my_catalog"),
    role_name: str = os.getenv("POLARIS_CATALOG_ROLE_NAME", "my_catalog_role"),
):
    payload = {
        "catalogRole": {"name": role_name},
    }
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.post(
            f"{polaris_catalog_mgmt_uri}/catalogs/{catalog_name}/catalog-roles",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info(
                f"Catalog Role '{role_name}' created for catalog '{catalog_name}'"
            )

    except requests.exceptions.RequestException as e:
        LOGGER.info(response.json())
        LOGGER.error(f"An error occurred: {e}")


def assign_catalog_role_to_principal_role(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    principal_role: str = os.getenv("POLARIS_PRINCIPAL_ROLE_NAME", "polarisuser_role"),
    catalog_role: str = os.getenv("POLARIS_CATALOG_ROLE_NAME", "my_catalog_role"),
    catalog_name: str = os.getenv("POLARIS_CATALOG_NAME", "my_catalog"),
):
    payload = {
        "catalogRole": {"name": catalog_role},
    }
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.put(
            f"{polaris_catalog_mgmt_uri}/principal-roles/{principal_role}/catalog-roles/{catalog_name}",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info(
                f"Catalog Role '{catalog_role}' assigned to Principal role '{principal_role}'"
            )

    except requests.exceptions.RequestException as e:
        print(response.json())
        print(f"An error occurred: {e}")


# Step 8: Assign Catalog Role to Principal Role
def grants_to_catalog_role_on_catalog(
    root_auth_token: str,
    polaris_catalog_mgmt_uri: str,
    catalog_role: str = os.getenv("POLARIS_CATALOG_ROLE_NAME", "my_catalog_role"),
    catalog_name: str = os.getenv("POLARIS_CATALOG_NAME", "my_catalog"),
    privilege: str = "CATALOG_MANAGE_CONTENT",
    type: str = "catalog",
):
    payload = {
        "grant": {
            "type": type,
            "privilege": privilege,
        },
    }
    payload_json = json.dumps(payload)
    LOGGER.debug(payload_json)
    try:
        response = requests.put(
            f"{polaris_catalog_mgmt_uri}/catalogs/{catalog_name}/catalog-roles/{catalog_role}/grants",
            headers=build_headers(root_auth_token),
            data=payload_json,
        )
        # Check if the request was successful
        response.raise_for_status()

        if response.status_code == 201:
            LOGGER.info(
                f"Grants '{privilege}' assigned to Catalog '{catalog_name}' role '{catalog_role}'"
            )

    except requests.exceptions.RequestException as e:
        print(response.json())
        print(f"An error occurred: {e}")


def generate_setup_notebook_cells(
    principal_client_id,
    principal_client_secret,
    catalog_name=os.getenv("POLARIS_CATALOG_NAME", "my_catalog"),
):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader("templates"))
    template_context = {
        "polaris_catalog_name": catalog_name,
        "principal_client_id": principal_client_id,
        "principal_client_secret": principal_client_secret,
    }
    notebook_template = env.get_template("setup_verify_notebook.ipynb.j2")
    content = notebook_template.render(template_context)

    template_out_dir = Path("notebooks")
    template_out_dir.mkdir(exist_ok=True)
    with open(template_out_dir.joinpath("polaris_setup_verify.ipynb"), "w") as f:
        f.write(content)


def run_steps() -> tuple[str, str]:
    # Get the root principal credentials from the Polaris Container logs
    client_id, client_secret = extract_root_principal_credentials()
    LOGGER.info(f"Client ID: {client_id},Client Secret: {client_secret}")
    polaris_api_host = os.getenv("POLARIS_API_HOST", "localhost")
    polaris_api_port = os.getenv("POLARIS_API_PORT", get_api_port(8181))
    # Generate the root auth token to be used with Management API
    root_auth_token = get_auth_token(
        client_id=client_id,
        client_secret=client_secret,
        polaris_api_host=polaris_api_host,
        polaris_api_port=polaris_api_port,
    )
    LOGGER.info(f"Root Auth Token: {root_auth_token}")
    polaris_catalog_mgmt_uri = (
        f"http://{polaris_api_host}:{polaris_api_port}/api/management/v1"
    )
    # Step 1: Create the Catalog
    create_catalog(
        root_auth_token=root_auth_token,
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
    )

    # Step 2: Create Principal
    principal_client_id, principal_client_secret = create_principal(
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
        root_auth_token=root_auth_token,
    )
    LOGGER.info(
        f"Principal Client ID: {principal_client_id}, Principal Client Secret: {principal_client_secret}"
    )
    # Step 3: Create Principal Role
    create_principal_role(
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
        root_auth_token=root_auth_token,
    )
    # Step 4: Assign Role to Principal
    assign_role_to_principal(
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
        root_auth_token=root_auth_token,
    )
    # Step 5: Create Catalog Role
    create_catalog_role(
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
        root_auth_token=root_auth_token,
    )
    # Step 6: Assign Catalog Role to Principal Role
    assign_catalog_role_to_principal_role(
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
        root_auth_token=root_auth_token,
    )
    # Step 7: Assign Grants to Catalog Role on Catalog
    grants_to_catalog_role_on_catalog(
        polaris_catalog_mgmt_uri=polaris_catalog_mgmt_uri,
        root_auth_token=root_auth_token,
    )


if __name__ == "__main__":
    LOGGER.info("Running Polaris Demo Setup")
    principal_client_id, principal_client_secret = run_steps()
    LOGGER.info("Generating Setup Verification Notebook Cells")
    generate_setup_notebook_cells(
        principal_client_id,
        principal_client_secret,
    )
