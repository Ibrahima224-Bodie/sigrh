from django.contrib.auth.models import Group


ROLE_GROUP_PREFIX = "ROLE::"


def get_role_group_name(role_code):
    return f"{ROLE_GROUP_PREFIX}{role_code}"


def get_role_group(role_code):
    if not role_code:
        return None
    group, created = Group.objects.get_or_create(name=get_role_group_name(role_code))
    return group


def get_role_group_names(role_choices):
    return [get_role_group_name(role_code) for role_code, _ in role_choices]


def get_manual_groups_queryset():
    return Group.objects.exclude(name__startswith=ROLE_GROUP_PREFIX).order_by("name")


def sync_user_role_group(user):
    if not getattr(user, "pk", None):
        return

    role_group_names = get_role_group_names(getattr(user, "ROLE_CHOICES", ()))
    if role_group_names:
        user.groups.remove(*Group.objects.filter(name__in=role_group_names))

    if getattr(user, "role", None):
        role_group = get_role_group(user.role)
        if role_group is not None:
            user.groups.add(role_group)