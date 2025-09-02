CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."BPA_POST_CD_RULES_IOF" INSTEAD OF
    INSERT OR DELETE OR UPDATE ON MDM_V_BPA_POST_CD_RULES_MTN REFERENCING OLD AS OLD NEW AS NEW
DECLARE
    V_TRIGGER_NAME    VARCHAR2 (40) := 'BPA_POST_CD_RULES_IOF';
    ERR_DEL EXCEPTION;
    ERR_POSTAL_CODE EXCEPTION;
    ERR_NULL EXCEPTION;
    CNTR              PLS_INTEGER;
    V_RULE_ID         V_BPA_POSTAL_CODE_RULES.RULE_ID %TYPE;
    V_PATTERN_ID      V_BPA_POSTAL_CODE_PATTERNS.PATTERN_ID %TYPE;
    V_PATTERN         V_BPA_POSTAL_CODE_PATTERNS.PATTERN %TYPE;
    V_ALLOWED_PATTERN VARCHAR2 (30) := '^[A|9|-| ]*$';
 
    --(A, 9, - and space)
BEGIN --
    V_PATTERN := :NEW.PATTERN;
 
    -- Check musst be null inconsistance
    CASE
        WHEN V_PATTERN IS NOT NULL THEN -- must be null check
            IF :NEW.RULE_FLAG = 'N' THEN
                RAISE ERR_NULL;
            END IF;
 
        -- Check allowed pattern entries
            IF NOT OWA_PATTERN.MATCH (V_PATTERN, V_ALLOWED_PATTERN) THEN
                RAISE ERR_POSTAL_CODE;
            END IF;
        ELSE
            IF :NEW.RULE_FLAG = 'M' THEN
                RAISE ERR_POSTAL_CODE;
            END IF;
    END CASE;
 

    -- check if entry exists on bpa_postal_code_rules table
    SELECT
        COUNT (*) INTO CNTR
    FROM
        V_BPA_POSTAL_CODE_RULES
    WHERE
        COUNTRY_CD = :NEW.COUNTRY_CD;
    IF CNTR = 0 THEN -- insert country rule when no entry found
        SELECT
            NVL (MAX (RULE_ID) + 1, 1) INTO V_RULE_ID
        FROM
            V_BPA_POSTAL_CODE_RULES;
        INSERT INTO V_BPA_POSTAL_CODE_RULES (
            RULE_ID,
            COUNTRY_CD,
            RULE_FLAG
        ) VALUES (
            V_RULE_ID,
            UPPER (:NEW.COUNTRY_CD),
            :NEW.RULE_FLAG
        );
    ELSE
        V_RULE_ID := :NEW.RULE_ID;
    END IF;
 

    -- Select next pattern id => used by insert
    SELECT
        NVL (MAX (PATTERN_ID) + 1, 1) INTO V_PATTERN_ID
    FROM
        V_BPA_POSTAL_CODE_PATTERNS;
    IF INSERTING AND V_PATTERN IS NOT NULL THEN -- insert into bpa_postal_code_patterns table
        INSERT INTO V_BPA_POSTAL_CODE_PATTERNS (
            PATTERN_ID,
            RULE_ID,
            PATTERN,
            DESCRIPTION,
            VALID_IND
        ) VALUES (
            V_PATTERN_ID,
            V_RULE_ID,
            V_PATTERN,
            :NEW.DESCRIPTION,
            :NEW.VALID_IND
        );
    ELSIF UPDATING THEN
        IF :OLD.RULE_FLAG != :NEW.RULE_FLAG THEN -- update  bpa_postal_code_rules table
            UPDATE V_BPA_POSTAL_CODE_RULES
            SET
                RULE_FLAG = :NEW.RULE_FLAG
            WHERE
                RULE_ID = V_RULE_ID;
        END IF;

        IF :NEW.PATTERN_ID IS NOT NULL THEN
            IF V_PATTERN IS NOT NULL THEN
                UPDATE V_BPA_POSTAL_CODE_PATTERNS
                SET
                    PATTERN = V_PATTERN,
                    DESCRIPTION = :NEW.DESCRIPTION,
                    VALID_IND = :NEW.VALID_IND
                WHERE
                    PATTERN_ID = :NEW.PATTERN_ID;
            ELSE
                DELETE FROM V_BPA_POSTAL_CODE_PATTERNS
                WHERE
                    PATTERN_ID = :NEW.PATTERN_ID
                    AND PATTERN = :OLD.PATTERN;
            END IF;
        ELSE
            IF V_PATTERN IS NOT NULL THEN
                INSERT INTO V_BPA_POSTAL_CODE_PATTERNS (
                    PATTERN_ID,
                    RULE_ID,
                    PATTERN,
                    VALID_IND
                ) VALUES (
                    V_PATTERN_ID,
                    V_RULE_ID,
                    V_PATTERN,
                    :NEW.VALID_IND
                );
            END IF;
        END IF;
    ELSIF DELETING THEN
        DELETE FROM GMD.V_BPA_POSTAL_CODE_PATTERNS
        WHERE
            PATTERN_ID = :OLD.PATTERN_ID;
    END IF;
EXCEPTION
    WHEN ERR_DEL THEN
        RAISE_APPLICATION_ERROR (-20112, V_TRIGGER_NAME);
    WHEN ERR_NULL THEN
        RAISE_APPLICATION_ERROR (-20114, V_TRIGGER_NAME);
    WHEN ERR_POSTAL_CODE THEN
        RAISE_APPLICATION_ERROR (-20119, V_TRIGGER_NAME);
END;