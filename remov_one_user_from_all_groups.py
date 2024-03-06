import requests
from gitLab_API import *


def find_user_by_email(email):
    """Find a user by their email and return their user ID."""
    users = fetch_from_gitlab(f'{target_gitlab_api}users?search={email}', headers=target_headers)
    for user in users:
        if user['email'] == email:
            return user['id']
    return None

def get_user_groups(user_id):
    """List all groups a user is a member of."""
    groups = fetch_from_gitlab(f'{target_gitlab_api}groups?min_access_level=10', headers=target_headers)
    user_groups = [group for group in groups if user_id in [member['id'] for member in requests.get(f'{target_gitlab_api}groups/{group["id"]}/members', headers=target_headers).json()]]
    return user_groups

def remove_user_from_group(user_id, group_id):
    """Remove a user from a group."""
    response = requests.delete(f'{target_gitlab_api}groups/{group_id}/members/{user_id}', headers=target_headers)
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
        members = requests.get(f'{target_gitlab_api}groups/{group["id"]}/members', headers=target_headers).json()
        if len(members) > 1:  # The user is not the only member
            remove_user_from_group(user_id, group['id'])
        else:
            print(f'User {user_id} is the only member in group {group["id"]}. Skipping.')

if __name__ == "__main__":
    main()
