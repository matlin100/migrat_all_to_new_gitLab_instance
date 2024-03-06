from gitLab_API import *
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

def update_progress(component):
    # Implement your progress updating logic here
    pass

def migrate_projects():
    projects = fetch_from_gitlab(f"{source_gitlab_api}/projects", source_headers)
    print(projects)
    migration_progress["projects"]["total"] = len(projects)
    print(f"Starting migration of {migration_progress['projects']['total']} projects...")

    for project in projects:
        export_project(project['id'])
        status = "none"
        while status != "finished":
            status = check_export_status(project['id'])
            time.sleep(10)  # Sleep for a while before checking again
        file_path = download_export(project['id'])
        sanitize_path = sanitize_namespace_path( project['path_with_namespace'])
        print(f"sanitize_path : {sanitize_path}")
        print(f" project['path_with_namespace'] :{ project['path_with_namespace']}")
        import_project_to_target(file_path, sanitize_path)

        # Post-import actions like migrating merge requests could go here
        # For simplicity, this example assumes immediate availability of the imported project,
        # which may not be the case. Adjust as needed based on actual import behavior.

        merge_requests = fetch_merge_requests(project['id'])
        # In a real scenario, you should map the old project ID to the new one.
        # Here, it's simplified and assumes identical project structure.
        migrate_merge_requests(merge_requests, project['id'])

        update_progress("projects")
# Main function to run migrations with summary
def main():
    try:
        migrate_users()
        migrate_groups()
        # migrate_projects()
        print("\nMigration completed successfully.")
        #print(f"Total users migrated: {migration_progress['users']['migrated']}/{migration_progress['users']['total']}")
        #print(f"Total groups migrated: {migration_progress['groups']['migrated']}/{migration_progress['groups']['total']}")
        print(f"Total projects migrated: {migration_progress['projects']['migrated']}/{migration_progress['projects']['total']}")
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == '__main__':
    main()
