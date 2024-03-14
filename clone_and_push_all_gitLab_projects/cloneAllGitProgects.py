import os
import requests

gitlab_url = 'http://gitlab/api/v4'
gitlab_token = 'DtdsoPoysuNAs4SeFmyb'


# Set the directory where you want to clone all the projects
clone_directory = r"S:\TeamFolders\Yechezkel\gitclone6"
if not os.path.exists(clone_directory):
    os.makedirs(clone_directory)

def sanitize_name(name):
    """Sanitize project name to ensure it's valid for Windows file system."""
    invalid_chars = '<>:"\\/|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name

def get_gitlab_projects(url, headers, page=1):
    """Fetch a list of projects from GitLab with pagination."""
    projects, next_page = [], None
    response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
    if response.status_code == 200:
        projects = response.json()
        if 'next' in response.links:
            next_page = page + 1
    else:
        print(f"Failed to fetch projects. Status code: {response.status_code}")
    print(f"projects : {len(projects)}")
    return projects, next_page

def clone_projects(projects):
    """Clone a list of GitLab projects."""
    for project in projects:
        repo_url = project["http_url_to_repo"]
        project_name = sanitize_name(project["path_with_namespace"])
        clone_path = os.path.join(clone_directory, project_name)
        if not os.path.exists(clone_path):
            print(f"Cloning {project['name']} into {clone_path}")
            clone_cmd = f'git clone "{repo_url}" "{clone_path}"'
            if os.system(clone_cmd) != 0:
                print(f"Failed to clone {project['name']}.")
        else:
            print(f"Directory {clone_path} already exists, skipping clone.")

# Prepare the request to fetch projects
gitlab_projects_url = f"{gitlab_url}/projects"
gitlab_headers = {"PRIVATE-TOKEN": gitlab_token}

# Fetch and clone all projects
page = 1
while page:
    projects, next_page = get_gitlab_projects(gitlab_projects_url, gitlab_headers, page)
    if projects:
        clone_projects(projects)
    page = next_page
    print(f"page : {page}")

print("All projects have been attempted to clone.")

