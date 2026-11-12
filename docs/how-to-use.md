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

## The "All Deltares" group

Every user is a member of the **All Deltares** group. The application creates this group on startup, adds all existing users to it, and adds each user again every time they log in with SSO. Removing a user from the group, or deleting the group, is undone on the next login or restart.

The group has the **data_producer** role for the whole application (not for one collection). This means every user can:

- add items to **every** collection;
- edit the items **they created themselves**;
- **not** delete items, and not change or delete collections.

## Items: who can add, edit and delete

The application stores who created each item (in the `itemowner` table). Items created before this was added have no recorded creator.

| Action | Allowed for |
|--------|-------------|
| Add an item | Anyone with `item:create` on the collection, or for the whole application (everyone, through All Deltares) |
| Edit an item | Anyone with `item:update` **on that collection** (e.g. Collection Data Steward); with only the whole-application role, just the items you created |
| Delete an item | Anyone with `item:delete` on that collection (Collection Data Steward) |
| Bulk upsert (`POST /collections/{collection_id}/bulk_items` with method `upsert`) | Only users with `item:update` on that collection, because it can overwrite other people's items |

`GET /owned-items` returns the items created by the logged-in user.
