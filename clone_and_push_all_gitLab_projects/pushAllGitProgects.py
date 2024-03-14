import requests
import os
from gitLab_API import *
import subprocess
import json


import subprocess
import os
import re
import requests

# Configuration: Update these variables with your information
base_gitlab_url = 'http://gitlab16.pituah.iaf/'
target_gitlab_api = target_gitlab_api
headers = target_headers
clone_directory = r"S:\TeamFolders\Yechezkel\gitclone"
log_file = r"C:\Users\matlin\PycharmProjects\cloneAllGitLab\logs\push_to_taget_log.json"
def log_event(log_file, project_name, status, message=None, error=None):
    log_entry = {
        "project_name": project_name,
        "status": status,
        "message": message,
        "error": error
    }
    try:
        with open(log_file, 'a') as file:
            json.dump(log_entry, file)
            file.write('\n')
    except IOError as e:
        print(f'error loding event: {e}')


def get_namespace_and_project_from_git_remote(repo_path):
    """Get the namespace and project name from a Git repository's remote URL."""
    os.chdir(repo_path)
    try:
        remote_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
    except subprocess.CalledProcessError:
        print("Error getting the remote URL. Is 'origin' set up?")
        return None, None
    match = re.search(r'[:/]([^:/]+)/([^/]+)\.git$', remote_url)
    if match:
        namespace = match.group(1)
        project_name = match.group(2)
        return namespace, project_name
    else:
        print("Unable to parse namespace and project name from the remote URL.")
        return None, None

def project_exists(namespace, project_name):
    """Check if the project exists on GitLab."""
    response = requests.get(f"{target_gitlab_api}projects/{namespace}%2F{project_name}", headers=headers)
    if response.status_code == 200:
        return True, response.json()['http_url_to_repo']
    return False, None

def create_project(namespace_id, project_name):
    """Create a project on GitLab."""
    data = {'name': project_name, 'namespace_id': namespace_id, 'visibility': 'private'}
    response = requests.post(f"{target_gitlab_api}projects", headers=headers, json=data)
    if response.status_code in [201, 200]:
        print(f"Project {project_name} created successfully.")
        return response.json()['http_url_to_repo']
    else:
        print(f"Failed to create project {project_name}. Response: {response.json()}")
        return None

def get_namespace_id(namespace):
    """Get the namespace ID from GitLab by its name."""
    response = requests.get(f"{target_gitlab_api}namespaces?search={namespace}", headers=headers)
    if response.status_code == 200 and response.json() or response.status_code == 201 and response.json():
        return response.json()[0]['id']
    else:
        print(f"Failed to find namespace {namespace}.")
        return None

def create_or_get_project(namespace, project_name):
    """Check if a project exists on GitLab, and create it if it does not."""
    exists, gitlab_project_url = project_exists(namespace, project_name)
    if exists:
        print(f"Project {project_name} exists. Using existing URL.")
        return gitlab_project_url

    namespace_id = get_namespace_id(namespace)
    if namespace_id:
        return create_project(namespace_id, project_name)
    else:
        return None

def push_to_project(repo_path, gitlab_project_url, project_name):
    """Push the local project to the GitLab project URL."""
    print(f"start Pushing to {gitlab_project_url}")
    os.chdir(repo_path)
    try:
        subprocess.run(['git', 'remote', 'remove', 'origin'], check=False)
        subprocess.run(['git', 'remote', 'add', 'origin', gitlab_project_url], check=True)
        subprocess.run(['git', 'push', '--all', 'origin'], check=True)
        subprocess.run(['git', 'push', '--tags', 'origin'], check=True)
        log_event(log_file=log_file, project_name=project_name, status="success",  error=f'no error success push {project_name}')
        print(f'successfully push {project_name}')
    except subprocess.CalledProcessError as e:
        log_event(log_file=log_file, project_name=project_name, status="failure", error=str(e))
        print(f'Failed to  push {project_name}')
def process_projects(clone_directory):
    """Process each project in the clone directory."""
    for project_dir in os.listdir(clone_directory):
        full_path = os.path.join(clone_directory, project_dir)
        if os.path.isdir(full_path):
            namespace, project_name = get_namespace_and_project_from_git_remote(full_path)
            if namespace and project_name:
                gitlab_project_url = create_or_get_project(namespace, project_name)
                if gitlab_project_url:
                    push_to_project(full_path, gitlab_project_url, project_name)

if __name__ == "__main__":
    process_projects(clone_directory)
