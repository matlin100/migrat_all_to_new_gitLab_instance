import re
import requests
import time

# Configuration
source_gitlab_api = "http://gitlab/api/v4/"
target_gitlab_api = "http://gitlab16/api/v4/"
source_headers = {"PRIVATE-TOKEN": "DtdsoPoysuNAs4SeFmyb"}
target_headers = {"PRIVATE-TOKEN": "glpat-2rdgXRKZd3xz4fHw6xwF"}

# Progress Tracking
migration_progress = {
    "users": {"total": 0, "migrated": 0},
    "groups": {"total": 0, "migrated": 0},
    "projects": {"total": 0, "migrated": 0}
}

# Utility Functions
def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limit hit, sleeping for {retry_after} seconds")
        time.sleep(retry_after)
        return True
    return False

def fetch_from_gitlab(url, headers):
    all_items = []
    page = 1
    per_page = 100

    while True:
        response = requests.get(f"{url}?page={page}&per_page={per_page}", headers=headers , params={'page': page, 'per_page': per_page})
        if handle_rate_limit(response):
           continue
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            all_items.extend(data)
            page += 1
        else:
            raise Exception(f"Failed t fetch data: {response.status_code}")
    return all_items
def post_to_gitlab(url, headers, data):
    while True:
        response = requests.post(url, headers=headers, data=data)
        if handle_rate_limit(response):
            continue
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 409:
            print(f"skipping migration for  due to conflict ")
            return None
        else:
            raise Exception(f"Failed to post data: {response.status_code}, {response.text}")

def sanitize_namespace_path(path):
    path = path.strip(".-_")
    path = re.sub(r"[-._]+", '-', path)
    return path
def sanitize_path(path):
    counter = 0
    path = re.sub(r'^[^a-zA-Z0-9]+[^a-zA-Z0-9]+$', '', path)
    path2 = re.sub(r'[^a-zA-Z0-9]+', '_', path)
    if(path != path2):
        counter = counter + 1
        print(f"{counter} :  {path2} > {path}")
    return path2

def update_progress(entity_type):
    migration_progress[entity_type]["migrated"] += 1
    print(f"{entity_type.capitalize()} migrated: {migration_progress[entity_type]['migrated']}/{migration_progress[entity_type]['total']}")

def export_project(project_id):
    response = requests.post(f"{source_gitlab_api}projects/{project_id}/export", headers=source_headers)
    if response.status_code in [200, 201, 202]:
        print(f"Export started for project {project_id}")
    else:
        raise Exception(f"Failed to start export for project {project_id}: {response.status_code}")

def check_export_status(project_id):
    response = requests.get(f"{source_gitlab_api}projects/{project_id}/export", headers=source_headers)
    if response.status_code == 200:
        return response.json()["export_status"]
    else:
        raise Exception(f"Failed to check export status for project {project_id}: {response.status_code}")

def download_export(project_id):
    response = requests.get(f"{source_gitlab_api}projects/{project_id}/export/download", headers=source_headers, stream=True)
    if response.status_code == 200:
        file_path = f"{project_id}.tar.gz"
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Project {project_id} downloaded")
        return file_path
    else:
        raise Exception(f"Failed to download export for project {project_id}: {response.status_code}")

def import_project_to_target(file_path, namespace):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'path': namespace}
        try:
            response = requests.post(f"{target_gitlab_api}projects/import", headers=target_headers, data=data, files=files)
            if response.status_code in [200, 201]:
                print(f"Import started for project in {namespace}")
            else:
                raise Exception(f"Failed to import project to {namespace}: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Exception during project import : {str(e)}")


def get_all_groups_users_from_new_gitLab():
    new_group_response = fetch_from_gitlab(f"{target_gitlab_api}groups", headers=target_headers)
    new_user_response = fetch_from_gitlab(f"{target_gitlab_api}users", headers=target_headers)
    new_group = {group['name']: group['id'] for group in new_group_response}if new_group_response else {}
    new_user = {user['username']: user['id'] for user in new_user_response}if new_user_response else {}
    return {**new_group, **new_user}


def get_alL_old_projects():
    return fetch_from_gitlab(f"{source_gitlab_api}projects", headers=source_headers)


