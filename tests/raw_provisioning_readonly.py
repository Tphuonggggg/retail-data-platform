"""Verify approved Raw DDL through SELECT-only runtime checks; never provision/load.

This checks the initial empty provisioned state, before any ingestion. A later
data-bearing capture needs its own row-count/reconciliation contract.

Offline: python -m unittest discover -s tests -p raw_provisioning_readonly.py
Runtime (explicit Owner authorization): python tests/raw_provisioning_readonly.py --verify --env-file .env
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from typing import Any
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from ingestion.common.config import settings
from ingestion.common.contracts import select_objects
from ingestion.loaders.postgres import PostgresTarget
from ingestion.loaders.schema import full_load_ddl


class VerificationError(Exception):
    """Messages contain only contract/metadata identifiers, never driver text."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def identifier(name: str) -> str:
    return ".".join(part[1:-1] if part.startswith('"') else part.lower() for part in name.strip().split("."))


def split_fields(body: str) -> list[str]:
    # This DDL contains no SQL comments inside CREATE TABLE bodies or escaped E strings.
    fields = []
    depth = 0
    quoted = None
    start = 0
    for index, character in enumerate(body):
        if quoted is not None:
            if character == quoted:
                quoted = None
        elif character in {"'", '"'}:
            quoted = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "," and depth == 0:
            fields.append(body[start:index].strip())
            start = index + 1
    require(depth == 0 and quoted is None, "UNSUPPORTED_DDL_BODY")
    return fields + [body[start:].strip()]


TOKEN = re.compile(r"\s*(::|>=|<=|<>|[()=~><,.;]|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|[A-Za-z_][A-Za-z0-9_]*|[0-9]+)")


def tokens(text: str) -> list[str]:
    result = []
    position = 0
    while position < len(text.rstrip()):
        match = TOKEN.match(text, position)
        require(match is not None, "UNSUPPORTED_DDL_EXPRESSION")
        assert match is not None
        value = match[1]
        result.append(value if value.startswith(("'", '"')) else value.lower())
        position = match.end()
    return result


def check_ast(text: str) -> tuple[Any, ...]:
    values = tokens(text)
    # PostgreSQL deparses implicit text literals with explicit ::text casts.
    values = [value for index, value in enumerate(values) if not
              (value == "::" and index + 1 < len(values) and values[index + 1] == "text") and not
              (value == "text" and index > 0 and values[index - 1] == "::")]
    position = 0

    def primary() -> tuple[Any, ...]:
        nonlocal position
        value = values[position]
        position += 1
        if value == "(":
            node = expression("or")
            require(values[position] == ")", "UNBALANCED_CHECK")
            position += 1
            return node
        if value.startswith("'"):
            return ("literal", value[1:-1].replace("''", "'"))
        if value.isdigit():
            return ("number", int(value))
        return ("identifier", identifier(value))

    def comparison() -> tuple[Any, ...]:
        nonlocal position
        left = primary()
        if position < len(values) and values[position] == "is":
            position += 1
            negated = position < len(values) and values[position] == "not"
            if negated:
                position += 1
            require(values[position] == "null", "UNSUPPORTED_IS_CHECK")
            position += 1
            return ("is_not_null" if negated else "is_null", left)
        if position < len(values) and values[position] in {"=", ">", "<", ">=", "<=", "<>", "~"}:
            operator = values[position]
            position += 1
            return (operator, left, primary())
        return left

    def expression(operator: str) -> tuple[Any, ...]:
        nonlocal position
        get = comparison if operator == "and" else lambda: expression("and")
        node = get()
        while position < len(values) and values[position] == operator:
            position += 1
            node = (operator, node, get())
        return node

    node = expression("or")
    require(position == len(values), "UNSUPPORTED_CHECK_TAIL")
    return node


def ddl_model(text: str) -> tuple[dict[str, Any], dict[str, str]]:
    tables = {}
    for match in re.finditer(r'CREATE TABLE\s+([\w.\"]+)\s*\((.*?)\);', text, re.S):
        name, body = identifier(match[1]), match[2]
        columns = []
        constraints = []
        for field in split_fields(body):
            if field.startswith(("PRIMARY KEY", "UNIQUE")):
                keys = tuple(identifier(key) for key in re.search(r"\((.*?)\)", field)[1].split(","))
                constraints.append(("p" if field.startswith("PRIMARY") else "u", keys))
                continue
            column = re.match(r'("\w+"|\w+)\s+([a-z]+(?:\([0-9,]+\))?(?:\[\])?)', field)
            require(column is not None, "UNSUPPORTED_COLUMN " + name)
            assert column is not None
            colname, kind = identifier(column[1]), column[2]
            default = re.search(r"\bDEFAULT\s+(.+?)(?=\s+(?:CHECK|REFERENCES|PRIMARY|UNIQUE)\b|$)", field)
            collation = 'C' if 'COLLATE "C"' in field else "default" if kind in {"text", "text[]"} else None
            columns.append({"name": colname, "type": {"timestamptz": "timestamp with time zone"}.get(kind, kind),
                            "not_null": "NOT NULL" in field or "PRIMARY KEY" in field,
                            "collation": collation, "default": default[1] if default else None})
            if "PRIMARY KEY" in field:
                constraints.append(("p", (colname,)))
            if re.search(r"\bUNIQUE\b", field):
                constraints.append(("u", (colname,)))
            reference = re.search(r'REFERENCES\s+([\w.\"]+)\(([^)]+)\)', field)
            if reference:
                constraints.append(("f", (colname,), identifier(reference[1]),
                                    tuple(identifier(key) for key in reference[2].split(","))))
            check_start = re.search(r"\bCHECK\s*\(", field)
            if check_start:
                require(field.endswith(")"), "UNSUPPORTED_CHECK_CLAUSE")
                constraints.append(("c", check_ast(field[check_start.end():-1])))
        primary = next(c[1] for c in constraints if c[0] == "p")
        for column in columns:
            column["not_null"] |= column["name"] in primary
        tables[name] = {"columns": columns, "constraints": constraints}
    views = {identifier(m[1]): m[2] for m in re.finditer(r'CREATE VIEW\s+([\w.\"]+)\s+AS\s+(.*?);', text, re.S)}
    require(len(tables) == 15 and len(views) == 11, "UNEXPECTED_DDL_SCOPE")
    return tables, views


def view_signature(text: str) -> tuple[str, ...]:
    # Approved views contain only column references and INNER JOIN equality predicates.
    # Grouping parentheses from pg_get_viewdef do not affect these joins/predicates.
    return tuple(identifier(v) if v.startswith('"') else v for v in tokens(text) if v not in {"(", ")", ";"})


def verify(env_file: Path) -> dict[str, Any]:
    import psycopg
    from psycopg import sql
    raw_text = (ROOT / "storage/raw/full_load.sql").read_text(encoding="utf-8")
    require(raw_text == full_load_ddl(), "DDL_GENERATOR_DRIFT")
    tables, views = ddl_model(raw_text)
    config = settings(env_file)
    c = config.target
    with psycopg.connect(host=c.host, port=c.port, dbname=c.database, user=c.user, password=c.password,
                         sslmode=c.sslmode, connect_timeout=5, autocommit=True,
                         options="-c default_transaction_read_only=on -c statement_timeout=10000",
                         application_name="retail_raw_provisioning_readonly_verify") as db:
        require(tuple(db.execute("SELECT current_database(),current_user,session_user").fetchone()) ==
                ("retail_raw", "retail_ingest", "retail_ingest"), "TARGET_IDENTITY")
        role = db.execute("SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                          "FROM pg_roles WHERE rolname=current_user").fetchone()
        require(tuple(role) == (True, False, False, False, False, False), "TARGET_ADMIN_FLAGS")
        loader = PostgresTarget(config)
        loader.connection = db
        loader.preflight(select_objects())  # SELECT-only; no source connection, lock or run registration.
        actual_inventory = {r[0]: r[1] for r in db.execute("SELECT n.nspname||'.'||c.relname,c.relkind "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname IN ('raw','ingestion_meta') AND c.relkind IN ('r','p','v','m')")}
        expected_inventory = {**{n: 'r' for n in tables}, **{n: 'v' for n in views},
                              'ingestion_meta.runs': 'r', 'ingestion_meta.object_runs': 'r'}
        require(actual_inventory == expected_inventory, "RELATION_INVENTORY")
        names_by_table = {}
        constraint_totals = Counter()
        column_count = index_count = 0
        for name, model in tables.items():
            rows = list(db.execute("SELECT a.attnum,a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull,"
                "co.collname,pg_get_expr(d.adbin,d.adrelid),a.attidentity,a.attgenerated "
                "FROM pg_attribute a LEFT JOIN pg_collation co ON co.oid=a.attcollation "
                "LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum "
                "WHERE a.attrelid=to_regclass(%s) AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum", (name,)))
            actual_columns = [{"name": r[1], "type": r[2], "not_null": r[3], "collation": r[4], "default": r[5]} for r in rows]
            require(actual_columns == model["columns"], "COLUMN_DEFINITION " + name)
            require(all(r[6] == r[7] == "" for r in rows), "IDENTITY_OR_GENERATED " + name)
            names = names_by_table[name] = {r[0]: r[1] for r in rows}
            column_count += len(rows)
            actual_constraints = []
            for kind, keys, refname, refkeys, expr, valid, deferred, initially, match, onupdate, ondelete in db.execute(
                "SELECT c.contype,c.conkey,c.confrelid::regclass::text,c.confkey,pg_get_expr(c.conbin,c.conrelid),"
                "c.convalidated,c.condeferrable,c.condeferred,c.confmatchtype,c.confupdtype,c.confdeltype "
                "FROM pg_constraint c WHERE c.conrelid=to_regclass(%s)", (name,)):
                require(valid and not deferred and not initially, "CONSTRAINT_VALIDITY " + name)
                if kind == 'n':
                    continue  # NOT NULL checked through every pg_attribute.attnotnull above.
                if kind in {'p', 'u'}:
                    value = (kind, tuple(names[k] for k in keys))
                elif kind == 'c':
                    value = ('c', check_ast(expr))
                elif kind == 'f':
                    ref = identifier(refname)
                    refcols = {r[0]: r[1] for r in db.execute("SELECT attnum,attname FROM pg_attribute "
                        "WHERE attrelid=to_regclass(%s) AND attnum>0", (ref,))}
                    require((match, onupdate, ondelete) == ('s', 'a', 'a'), "FK_ACTION " + name)
                    value = ('f', tuple(names[k] for k in keys), ref, tuple(refcols[k] for k in refkeys))
                else:
                    raise VerificationError("UNEXPECTED_CONSTRAINT " + name)
                actual_constraints.append(value)
                constraint_totals[kind] += 1
            require(Counter(actual_constraints) == Counter(model['constraints']), "CONSTRAINT_DEFINITION " + name)
            actual_indexes = []
            for primary, unique, valid, ready, immediate, count, total, keys, plain, unfiltered, method in db.execute(
                "SELECT i.indisprimary,i.indisunique,i.indisvalid,i.indisready,i.indimmediate,i.indnkeyatts,i.indnatts,"
                "i.indkey::int2[],i.indexprs IS NULL,i.indpred IS NULL,am.amname "
                "FROM pg_index i JOIN pg_class ix ON ix.oid=i.indexrelid JOIN pg_am am ON am.oid=ix.relam "
                "WHERE i.indrelid=to_regclass(%s)", (name,)):
                require(unique and valid and ready and immediate and count == total and plain and unfiltered
                        and method == 'btree', "INDEX_PROPERTIES " + name)
                actual_indexes.append(('p' if primary else 'u', tuple(names[k] for k in keys)))
            required_indexes = [c for c in model['constraints'] if c[0] in {'p', 'u'}]
            require(Counter(actual_indexes) == Counter(required_indexes), "INDEX_DEFINITION " + name)
            index_count += len(actual_indexes)
        for name, expected in views.items():
            actual = db.execute("SELECT pg_get_viewdef(to_regclass(%s),true)", (name,)).fetchone()[0]
            require(view_signature(actual) == view_signature(expected), "VIEW_DEFINITION " + name)
            base = identifier(re.search(r'FROM\s+([\w.\"]+)\s+p\b', expected)[1])
            wanted_columns = [(c['name'], c['type'], c['collation']) for c in tables[base]['columns']]
            actual_columns = [tuple(r) for r in db.execute("SELECT a.attname,format_type(a.atttypid,a.atttypmod),co.collname "
                "FROM pg_attribute a LEFT JOIN pg_collation co ON co.oid=a.attcollation "
                "WHERE a.attrelid=to_regclass(%s) AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum", (name,))]
            require(actual_columns == wanted_columns, "VIEW_COLUMNS " + name)
        for name in {**tables, **views}:
            owner, rls = db.execute("SELECT pg_get_userbyid(relowner),relrowsecurity FROM pg_class "
                                    "WHERE oid=to_regclass(%s)", (name,)).fetchone()
            require(owner == 'postgres' and not rls, "OWNER_OR_RLS " + name)
            wanted = {'SELECT'} if name in views else {'SELECT', 'UPDATE'} if name == 'ingestion_meta.raw_current' else {'SELECT', 'INSERT'}
            for permission in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER', 'MAINTAIN'):
                granted = db.execute('SELECT has_table_privilege(current_user,%s,%s)', (name, permission)).fetchone()[0]
                require(granted == (permission in wanted), "EFFECTIVE_PRIVILEGE " + name)
            for grantee, grantable in db.execute("SELECT a.grantee::regrole::text,a.is_grantable FROM pg_class c "
                "CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl,acldefault('r',c.relowner))) a WHERE c.oid=to_regclass(%s)", (name,)):
                require(grantee in {'postgres', 'retail_ingest'} and not grantable, "UNEXPECTED_ACL_GRANTEE " + name)
        counts = {}
        for name in {**tables, **views, 'ingestion_meta.runs': None, 'ingestion_meta.object_runs': None}:
            count = db.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(*name.split('.')))).fetchone()[0]
            require(count == (1 if name == 'ingestion_meta.raw_current' else 0), "UNEXPECTED_ROWS " + name)
            counts[name] = count
        pointer = db.execute('SELECT singleton,publication_id FROM ingestion_meta.raw_current').fetchall()
        require(pointer == [(True, None)], "INITIAL_POINTER")
        return {'status': 'RAW_PAYLOAD_SCHEMA_VERIFIED',
                'script_sha256': hashlib.sha256((ROOT / 'storage/raw/full_load.sql').read_bytes()).hexdigest(),
                'payload_tables': 11, 'control_tables': 4,
                'serving_views': 11, 'new_columns_verified': column_count, 'constraints': dict(constraint_totals),
                'new_indexes_verified': index_count, 'owner_and_grants': 'PASS_ALL_26_OBJECTS',
                'target_preflight': 'PASS_ALL_11', 'row_counts': counts, 'initial_pointer': 'TRUE_NULL',
                'read_only': db.execute('SHOW default_transaction_read_only').fetchone()[0],
                'full_load_executed': False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Open an explicitly read-only Raw connection')
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    args = parser.parse_args(argv)
    if not args.verify:
        parser.print_help()
        return 0
    try:
        print(json.dumps(verify(args.env_file)))
        return 0
    except VerificationError as error:
        print(json.dumps({'status': 'VERIFICATION_FAIL', 'category': str(error)}))
        return 1
    except Exception as error:
        print(json.dumps({'status': 'VERIFICATION_ERROR', 'error_type': type(error).__name__}))
        return 1


class DdlModelTests(unittest.TestCase):
    def test_actual_approved_ddl_scope_and_column_constraints(self):
        tables, views = ddl_model((ROOT / 'storage/raw/full_load.sql').read_text(encoding='utf-8'))
        self.assertEqual((len(tables), len(views)), (15, 11))
        self.assertEqual(sum(len(t['columns']) for t in tables.values()), 248)
        self.assertEqual(Counter(c[0] for t in tables.values() for c in t['constraints']),
                         {'p': 15, 'u': 10, 'f': 16, 'c': 34})

    def test_deparsed_casts_and_parentheses_preserve_temporal_check(self):
        self.assertEqual(check_ast('"ValidFrom" IS NULL OR "ValidFrom" ~ \'abc\\.def\''),
                         check_ast('(("ValidFrom" IS NULL) OR ("ValidFrom" ~ \'abc\\.def\'::text))'))
        self.assertNotEqual(check_ast('a>0 OR b>0 AND c>0'), check_ast('(a>0 OR b>0) AND c>0'))

    def test_constraint_and_view_drift_are_detectable(self):
        self.assertNotEqual(check_ast('row_count >= 0'), check_ast('row_count > 0'))
        self.assertNotEqual(check_ast('singleton'), check_ast('NOT_singleton'))
        self.assertEqual(view_signature('SELECT p.x FROM raw."orders" p WHERE (p.x);'),
                         view_signature(' SELECT p.x FROM raw.orders p WHERE p.x;'))
        self.assertNotEqual(view_signature('SELECT p.x FROM raw.orders p WHERE p.x;'),
                            view_signature('SELECT p.x FROM raw.orders p;'))

    def test_default_cli_never_connects(self):
        with patch('psycopg.connect') as connect, redirect_stdout(io.StringIO()):
            self.assertEqual(main([]), 0)
        connect.assert_not_called()


if __name__ == '__main__':
    raise SystemExit(main())
