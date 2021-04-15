import os
import logging

from jinja2.ext import Extension, InternationalizationExtension

try:
    from babel.core import Locale
    from babel.support import Translations, NullTranslations
    has_babel = True
except ImportError:
    has_babel = False

log = logging.getLogger(__name__)
base_path = os.path.dirname(os.path.abspath(__file__))


class NoBabelExtension(InternationalizationExtension):
    def __init__(self, environment):
        Extension.__init__(self, environment)
        environment.extend(
            install_null_translations=self._install_null,
            newstyle_gettext=False,
        )


def install_translations(env, config):
    if has_babel:
        locale = Locale.parse(config['theme']['locale'], sep='_')

        env.add_extension('jinja2.ext.i18n')
        translations = _get_merged_translations(config['theme'].dirs, 'locales', locale)
        if translations is not None:
            env.install_gettext_translations(translations)
        else:
            env.install_null_translations()
    else:
        # no babel installed, add dummy support for trans/endtrans blocks
        env.add_extension(NoBabelExtension)
        env.install_null_translations()


def _get_merged_translations(theme_dirs, locales_dir, locale):
    merged_translations = None

    log.debug("Looking for translations for locale '%s'", locale)
    for theme_dir in reversed(theme_dirs):
        dirname = os.path.join(theme_dir, locales_dir)
        translations = Translations.load(dirname, [locale])

        if type(translations) is NullTranslations:
            log.debug("No translations found here: '%s'", dirname)
            continue

        log.debug("Translations found here: '%s'", dirname)
        if merged_translations is None:
            merged_translations = translations
        else:
            merged_translations.merge(translations)

    return merged_translations
