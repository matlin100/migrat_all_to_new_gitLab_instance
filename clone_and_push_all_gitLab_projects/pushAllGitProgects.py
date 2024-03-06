import os.path

from gitLab_API import *
import subprocess

clone_directory = r"S:\TeamFolders\Yechezkel\gitclone"
new_gitlab_token = "glpat-2rdgXRKZd3xz4fHw6xwF"

def get_namespace_mapping():
    old_projects = get_alL_old_projects()
    new_groups = get_all_groups_users_from_new_gitLab()


    namespace_mapping = {}
    for project in old_projects:
        old_namespace = project['namespace']['name']
        if old_namespace in new_groups:
            namespace_mapping[project['name']] = new_groups[old_namespace]
        else:
            print(f"no matching namespace fund for {old_namespace} in the new git lab")
    return namespace_mapping



def get_old_repo_visibility():
    """Retrieve the visibility of a repository from the old GitLab instance."""
    url = f"{source_gitlab_api}projects/{repo_name.replace(' ', '%20')}"  # URL encode spaces
    response = requests.get(url, headers=source_headers)
    if response.status_code == 200:
        return response['visibility']
    else:
        print(f"Failed to retrieve visibility for repository {repo_name}. Response: {response.text}")
        return 'private'  # Default to private if unable to fetch

def create_new_repository(repo_name, namespace_id, visibility):
    """Create a new repository on the new GitLab instance with the specified visibility."""
    url = f"{target_gitlab_api}/api/v4/projects"
    payload = {
        'name': repo_name,
        'namespace_id': namespace_id,
        'visibility': visibility
    }
    response = requests.post(url, headers=target_headers, data=payload)
    if response.status_code == 201:
        print(f"Repository {repo_name} created on new GitLab instance with {visibility} visibility.")
        return response['http_url_to_repo']
    else:
        print(f"Failed to create repository {repo_name}. Response: {response.text}")
        return None

def push_repo_to_new_instance(local_path, new_remote_url):
    """Push all branches and tags from the local repository to the new GitLab instance."""
    os.chdir(local_path)
    subprocess.run(['git', 'remote', 'add', 'new-origin', new_remote_url], check=True)
    subprocess.run(['git', 'push', '--all', 'new-origin'], check=True)
    subprocess.run(['git', 'push', '--tags', 'new-origin'], check=True)

# Main script
if __name__ == "__main__":
    namespace_mapping = get_namespace_mapping()
    repos = [d for d in os.listdir(clone_directory) if os.path.isdir(os.path.join(clone_directory, d))]
    for repo_name in repos:
        if repo_name in namespace_mapping:
            namespace_id = namespace_mapping[repo_name]
            old_visibility = get_old_repo_visibility(repo_name)  # Retrieve old repo visibility
            repo_path = os.path.join(clone_directory, repo_name)
            print(f"repo_name {repo_name}")
            print(f"namespace_id :{ namespace_id}")
            new_repo_url = create_new_repository(repo_name, namespace_id, old_visibility)
            if new_repo_url:
                new_repo_url_with_token = new_repo_url.replace('https://', f'https://oauth2:{new_gitlab_token}@')
                print(f"new_repo_url_with_token : {new_repo_url_with_token}")
                push_repo_to_new_instance(repo_path, new_repo_url_with_token)
        else:
            print(f"No namespace mapping found for {repo_name}, skipping...")
