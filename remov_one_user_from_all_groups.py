import requests
import time
# Configuration
gitlab_api = 'http://gitlab16/api/v4/'
private_token = 'glpat-Qyj5s871bSzdwWhLV8CA'  # GitLab private token with admin or appropriate permissions
headers = {'Private-Token': private_token}


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
        response = requests.get(f"{url}&page={page}&per_page={per_page}", headers=headers)
        if handle_rate_limit(response):
           continue
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        all_items.extend(data)
        page += 1
    return all_items


def find_user_by_email(email):
    """Find a user by their email and return their user ID."""
    users = fetch_from_gitlab(f'{gitlab_api}users?search={email}', headers=headers)
    for user in users:
        if user['email'] == email:
            return user['id']
    return None

def get_user_groups(user_id):
    """List all groups a user is a member of."""
    groups = fetch_from_gitlab(f'{gitlab_api}groups?min_access_level=10', headers=headers)
    user_groups = [group for group in groups if user_id in [member['id'] for member in requests.get(f'{gitlab_api}groups/{group["id"]}/members', headers=headers).json()]]
    return user_groups

def remove_user_from_group(user_id, group_id):
    """Remove a user from a group."""
    response = requests.delete(f'{gitlab_api}groups/{group_id}/members/{user_id}', headers=headers)
    if response.status_code == 204:
        print(f'Removed user {user_id} from group {group_id}.')
    else:
        print(f'Failed to remove user {user_id} from group {group_id}.')

def main():
    user_email = 'matlin@pituah.iaf'
    user_id = find_user_by_email(user_email)
    if user_id is None:
        print(f'User with email {user_email} not found.')
        return

    user_groups = get_user_groups(user_id)
    for group in user_groups:
        members = requests.get(f'{gitlab_api}groups/{group["id"]}/members', headers=headers).json()
        if len(members) > 1:  # The user is not the only member
            remove_user_from_group(user_id, group['id'])
        else:
            print(f'User {user_id} is the only member in group {group["id"]}. Skipping.')

if __name__ == "__main__":
    main()
