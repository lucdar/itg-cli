
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="ITG_CLI",  # export envvars with `export ITG_CLI_FOO=bar`.
    settings_files=['settings.toml', '.secrets.toml'],  # Load these files in the order.
    validators=[
        # TODO: settings validation (see: https://www.dynaconf.com/validation/)
    ]
)
