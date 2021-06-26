from accounts.services import UserService
def user_changed(sender, instance, **kwargs):
    # import locally to avoid dependency cycle
    UserService.invalidate_user(instance.id)

def profile_changed(sender, instance, **kwargs):
    UserService.invalidate_profile(instance.user_id)