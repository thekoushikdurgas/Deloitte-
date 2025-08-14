README.md Fixing Guide
===================

The current issue in README.md is with the JSON example on line 164. The issue is related to the nested quotes in the SQL string.

To fix this:

1. Open README.md in a text editor
2. Go to line 164
3. Locate this line:
   ```
   "sql": "DO $$ DECLARE v_counter integer; v_description varchar(500); v_userid varchar(30); BEGIN IF (SUBSTRING(:new_theme_no FROM 1 FOR 1) !~ '^[0-9]$') THEN RAISE EXCEPTION \"Invalid theme number\"; END IF; v_userid := :ins_user; INSERT INTO themes(theme_no, registrat_date, theme_desc) VALUES (:new_theme_no, CURRENT_DATE, :new_theme_desc); END $$;"
   ```

4. Replace it with one of these options:

Option 1 (Using JSON string escaping):
```
"sql": "DO $$ DECLARE v_counter integer; v_description varchar(500); v_userid varchar(30); BEGIN IF (SUBSTRING(:new_theme_no FROM 1 FOR 1) !~ '^[0-9]$') THEN RAISE EXCEPTION 'Invalid theme number'; END IF; v_userid := :ins_user; INSERT INTO themes(theme_no, registrat_date, theme_desc) VALUES (:new_theme_no, CURRENT_DATE, :new_theme_desc); END $$;"
```

Option 2 (Using triple quotes for the JSON example):
```
"""
{
    "on_insert": [
        {
            "type": "sql",
            "sql": "DO $$ DECLARE v_counter integer; v_description varchar(500); v_userid varchar(30); BEGIN IF (SUBSTRING(:new_theme_no FROM 1 FOR 1) !~ '^[0-9]$') THEN RAISE EXCEPTION 'Invalid theme number'; END IF; v_userid := :ins_user; INSERT INTO themes(theme_no, registrat_date, theme_desc) VALUES (:new_theme_no, CURRENT_DATE, :new_theme_desc); END $$;"
        }
    ]
}
"""
```

The main issue is that the CssSyntaxError is being caused by the nested quotes in the JSON example. Either properly escaping them or using a different code block format should resolve the issue.

Once you've made the change, verify with the linting tool to make sure all errors are resolved.
