class LegacyRouter:
    """
    Route legacy app models to the 'legacy' database.
    Django internal apps go to 'default'.
    """

    legacy_apps = {'apis'}  # your app names containing legacy models

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.legacy_apps:
            return 'legacy'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.legacy_apps:
            return 'legacy'
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):

        # legacy apps should never migrate
        if app_label in self.legacy_apps:
            return False
        # all other apps migrate only to default DB
        return db == 'default'