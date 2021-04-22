import os
import logging

from jinja2.ext import Extension, InternationalizationExtension
from mkdocs.config.base import ValidationError

try:
    from babel.core import Locale, UnknownLocaleError
    from babel.support import Translations, NullTranslations
    has_babel = True
except ImportError:
    from typing import NamedTuple
    from string import ascii_letters
    has_babel = False


    class UnknownLocaleError(Exception):
        pass


    class Locale(NamedTuple):
        language: str
        territory: str = ''

        def __str__(self):
            if self.territory:
                return f'{self.language}_{self.territory}'
            return self.language

        @classmethod
        def parse(cls, identifier, sep):
            if not isinstance(identifier, str):
                raise TypeError("Unexpected value for identifier: '{identifier}'")
            locale = cls(*identifier.split(sep, 1))
            if not all(x in ascii_letters for x in locale.language):
                raise ValueError("expected only letters, got '{instance.language'")
            if len(locale.language) != 2:
                raise UnknownLocaleError("unknown locale '{instance}'")
            return locale


log = logging.getLogger(__name__)
base_path = os.path.dirname(os.path.abspath(__file__))


class NoBabelExtension(InternationalizationExtension):
    def __init__(self, environment):
        Extension.__init__(self, environment)
        environment.extend(
            install_null_translations=self._install_null,
            newstyle_gettext=False,
        )


def parse_locale(locale):
    try:
        return Locale.parse(locale, sep='_')
    except (ValueError, UnknownLocaleError, TypeError) as e:
            raise ValidationError(f'Invalid value for locale: {str(e)}')


def install_translations(env, locale, theme_dirs):
    if has_babel:
        env.add_extension('jinja2.ext.i18n')
        translations = _get_merged_translations(theme_dirs, 'locales', locale)
        if translations is not None:
            env.install_gettext_translations(translations)
        else:
            env.install_null_translations()
            if locale.language != 'en':
                log.warning(
                    f"No translations could be found for the locale '{locale}'. "
                    'Defaulting to English.'
                )
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
