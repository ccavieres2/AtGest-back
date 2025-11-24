# accounts/utils.py
def get_data_owner(user):
    """
    Si el usuario es mecánico, retorna a su jefe (employer).
    Si el usuario es dueño, retorna al mismo usuario.
    """
    if hasattr(user, 'profile') and user.profile.employer:
        return user.profile.employer
    return user