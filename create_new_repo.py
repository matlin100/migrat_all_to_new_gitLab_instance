from gitLab_API import *
import requests
import time
# Configuration for the old and new GitLab instances\

failed =[]
success = []
exist = []
# Retrieve all projects from the old GitLab instance
old_projects = fetch_from_gitlab(f'{source_gitlab_api}projects', headers=source_headers)
print(f'length old projects : {len(old_projects)}')
new_projects = fetch_from_gitlab(f'{target_gitlab_api}projects', headers=target_headers)
print(f'length new projects : {len(new_projects)}')

new_projects_path_name = [project['name'] for project in new_projects]
for project in old_projects:

    if project['name'] not in new_projects_path_name:
        # Create a new project in the new GitLab instance with the same details
        print(f"{project['name']} id { project['namespace']['id']}")
        new_project_data = {
            'name': project['name'],
            'path': project['path'],
            'namespace_id': project['namespace']['id'],  # You may need to map old namespace ID to new namespace ID
            'description': project['description'],
            'visibility': project['visibility'],
            'merge_requests_enabled': project['merge_requests_enabled'],
            'issues_enabled': project['issues_enabled'],
            'wiki_enabled': project['wiki_enabled'],
            'jobs_enabled': project['jobs_enabled'],
            'snippets_enabled': project['snippets_enabled'],
            # Add other settings you need to replicate
        }
        time.sleep(1)
        # Create the project in the new GitLab
        res = requests.post(f"{target_gitlab_api}projects", headers=target_headers, data=new_project_data)
        if res.status_code == 201 | res.status_code == 200:
            print(f'Created new project: {project["name"]}')
            success.append(project['name'])
        else:
            print(f"failed to Created new project: {project['name']} status code {res} .")
            print(new_project_data)
            failed.append(project['name'])
    else:
        exist.append(project['name'])
print(f"success :{len(success)}) {success}")
print(f'failed :{len(failed)}) {failed}')
print(f'exist :{len(exist)}) {exist}')
