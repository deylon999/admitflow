"""Compare frozen CHECK definitions without guessing SQL equivalence."""
import re
from uuid import uuid4

import sqlalchemy as sa


_TOKENS = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|[a-zA-Z_][a-zA-Z_0-9]*|[0-9]+|<>|!=|<=|>=|::|\S")


def _sql_tokens(sql):
    # Whitespace/case are insignificant outside quoted literals/identifiers only.
    return tuple(token if token.startswith(("'", '"')) else token.lower()
                 for token in _TOKENS.findall(sql))


def _reflected_checks(bind, name):
    return {
        (_sql_tokens(check['sqltext']),
         bool(check.get('dialect_options', {}).get('not_valid')),
         bool(check.get('dialect_options', {}).get('no_inherit')))
        for check in sa.inspect(bind).get_check_constraints(name)
    }


def checks_match(bind, table):
    actual = _reflected_checks(bind, table.name)
    checks = [item for item in table.constraints if isinstance(item, sa.CheckConstraint)]
    if bind.dialect.name != 'postgresql':
        expected = {(_sql_tokens(str(check.sqltext)), False, False) for check in checks}
        return actual == expected
    if not checks:
        return not actual

    # pg_get_constraintdef is a decompilation: parentheses, casts and IN/ANY can
    # differ from the migration SQL. Let the same server render BOTH sides.
    # No user rows, foreign keys or domain tables are copied or altered here.
    probe = sa.Table(
        f'_admitflow_check_{uuid4().hex}', sa.MetaData(),
        *(sa.Column(column.name, column.type) for column in table.columns),
        *(sa.CheckConstraint(str(check.sqltext)) for check in checks),
        prefixes=['TEMPORARY'], postgresql_on_commit='DROP',
    )
    probe.create(bind)
    try:
        return actual == _reflected_checks(bind, probe.name)
    finally:
        probe.drop(bind)
