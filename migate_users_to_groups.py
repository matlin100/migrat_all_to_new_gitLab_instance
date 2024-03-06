from gitLab_API import *
def get_user_id_map():
    source_users = fetch_from_gitlab(f"{source_gitlab_api}users?", source_headers)
    target_users = fetch_from_gitlab(f"{target_gitlab_api}users?", target_headers)
    source_email_to_id = {user['email']: user['id'] for user in source_users}
    print(source_email_to_id)
    target_email_to_id = {user['email']: user['id'] for user in target_users}
    print(target_email_to_id)
    # Create a mapping from source user ID to target user ID based on email
    user_id_map = {source_id: target_email_to_id[email] for email, source_id in source_email_to_id.items() if email in target_email_to_id}
    print(user_id_map)
    return user_id_map

def migrate_group_memberships():
    user_id_map = get_user_id_map()  # Dynamically create the user ID mapping
    source_groups = fetch_from_gitlab(f"{source_gitlab_api}groups?", source_headers)
    for group in source_groups:
        members = fetch_from_gitlab(f"{source_gitlab_api}groups/{group['id']}/members?", source_headers)
        for member in members:
            target_user_id = user_id_map.get(member['id'])  # Get the corresponding target user ID
            print(target_user_id)
            if not target_user_id:
                continue

            # Find the target group ID based on group path
            target_groups = fetch_from_gitlab(f"{target_gitlab_api}groups?search={group['path']}&", target_headers)
            target_group = next((g for g in target_groups if g['path'] == group['path']), None)

            if not target_group:
                print(f"Target group {group['path']} not found. Skipping...")
                continue

            member_data = {
                "user_id": target_user_id,
                "access_level": member['access_level']
            }
            result = post_to_gitlab(f"{target_gitlab_api}groups/{target_group['id']}/members", target_headers, member_data)

            if result:
                print(f"Added user {target_user_id} to group {target_group['path']}.")
            else:
                print(f"Failed to add user {target_user_id} to group {target_group['path']}.")

if __name__ == '__main__':
    migrate_group_memberships()
