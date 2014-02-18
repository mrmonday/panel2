import panel2_environment

from panel2.user import User, Permission, get_all_permissions

perms = get_all_permissions()

users = User.query.filter_by(is_admin=True).all()
for user in users:
    print "====", user.username, "===="
    for perm in perms.keys():
        if not user.has_permission(perm):
            print "Granting", perm, "to", user.username
            Permission(user, perm)
