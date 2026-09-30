# How to use

## Users list

There is no separate “create user” action in the application.

The users list (including the dropdown when adding people to a group) is filled from the database `User` table. That table is updated when people **log in with SSO**: on first successful login they are inserted automatically. Users listed in the `admin_users` configuration are also created on application startup.

Until someone has logged in at least once (or been seeded as an admin), they will not appear in the dropdown and cannot be added to a group.

## Groups and permissions

SSO login alone does **not** grant the right to manage groups. Rights come from **roles** assigned to groups the user belongs to.

| Action | Required permission | Who has it |
|--------|---------------------|------------|
| Create / update / delete groups | `group:create` / `group:update` / `group:delete` | Admin, Application Data Steward |
| Add / remove users from a group | `global:group_role:assign` | Admin only |
| Assign roles to a group | `global:group_role:assign` | Admin only |

A user who has signed in but is not in a group with one of these roles will get a **403 Forbidden** response when trying to perform these actions.
