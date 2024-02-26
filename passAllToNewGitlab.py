import requests
import time

# Configuration
source_gitlab_api = "http://gitlab/api/v4/"
target_gitlab_api = "http://gitlab16/api/v4/"
source_headers = {"PRIVATE-TOKEN": "DtdsoPoysuNAs4SeFmyb"}
target_headers = {"PRIVATE-TOKEN": "glpat-Qyj5s871bSzdwWhLV8CA"}

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
        response = requests.get(f"{url}?page={page}&per_page={per_page}", headers=headers)
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
        response = requests.post(url, headers=headers, json=data)
        if handle_rate_limit(response):
            continue
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 409:
            print(f"skipping migration for {data['username']} due to conflict : {response.json().get('message')} ")
            return None
        else:
            raise Exception(f"Failed to post data: {response.status_code}, {response.text}")

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

# Migration Functions with Enhanced Progress Tracking
def migrate_users():
    users = fetch_from_gitlab(f"{source_gitlab_api}users", source_headers)
    migration_progress["users"]["total"] = len(users)
    print(f"Starting migration of {migration_progress['users']['total']} users...")
    for user in users:
        user_data = {
            "email": user["email"],
            "username": user["username"],
            "name": user["name"],
            "password": "Aa123456789",
            "skip_confirmation": True,
            "force_random_password": False,
            "reset_password": False
        }
        try:
            result = post_to_gitlab(f"{target_gitlab_api}users", target_headers, user_data)
            if result.get('message').startswith("Email hes already been taken"):
                print(f"skipping migration for {user['username']}  due conflict : email has been taken")
                continue
            if result is not None:
                update_progress("users")
        except Exception as e:
            if "Email hes already been taken" in str(e) or "Username hes already been taken" in str(e):
               print(f"skipping migration for {user['username']}  due conflict : {str(e)}")
            else:
                 print(f"failed to migration {user['username']} : {str(e)}")
def migrate_groups():
    groups = fetch_from_gitlab(f"{source_gitlab_api}groups", source_headers)
    migration_progress["groups"]["total"] = len(groups)
    print(f"Starting migration of {migration_progress['groups']['total']} groups...")
    for group in groups:
        exiting_groups = fetch_from_gitlab(f"{target_gitlab_api}groups?search={group['path']}", target_headers)
        if any(g['path'] == group['path'] for g in exiting_groups):
            print(f"skipping migration for groups {group['path']} due to conflict : Path already been taken")
            continue
        group_data = {
            "name": group["name"],
            "path": group["path"],
        }
        try:
            post_to_gitlab(f"{target_gitlab_api}groups", target_headers, group_data)
            update_progress("groups")
        except Exception as e:
            if 'has already been taken' in str(e):
                print(f'Skipping migration for group {group["path"]} due to conflict path has already been taken')
            else:
                print(f"failed to migrate group{group['path']}: {str(e)}")
def migrate_projects():
    projects = fetch_from_gitlab(f"{source_gitlab_api}projects", source_headers)
    migration_progress["projects"]["total"] = len(projects)
    print(f"Starting migration of {migration_progress['projects']['total']} projects...")
    for project in projects:
        export_project(project['id'])
        status = "none"
        while status != "finished":
            status = check_export_status(project['id'])
            time.sleep(10)  # Sleep for a while before checking again
        file_path = download_export(project['id'])
        import_project_to_target(file_path, project['path_with_namespace'])
        update_progress("projects")

def migrate_group_members(group_id, members):
    for member in members:
        target_user_id = s


# Main function to run migrations with summary
def main():
    try:
        migrate_users()
        #migrate_groups()
        #migrate_projects()
        print("\nMigration completed successfully.")
        #print(f"Total users migrated: {migration_progress['users']['migrated']}/{migration_progress['users']['total']}")
        #print(f"Total groups migrated: {migration_progress['groups']['migrated']}/{migration_progress['groups']['total']}")
        print(f"Total projects migrated: {migration_progress['projects']['migrated']}/{migration_progress['projects']['total']}")
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == '__main__':
    main()
