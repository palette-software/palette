from controller.credential import CredentialEntry

class CredentialMixin(object):

    PRIMARY_KEY = 'primary'
    SECONDARY_KEY = 'secondary'
    READONLY_KEY = 'readonly'

    def get_cred(self, envid, name):
        return CredentialEntry.get_by_envid_key(envid, name, default=None)
