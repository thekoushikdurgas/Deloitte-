CREATE OR REPLACE TRIGGER COMPREHENSIVE_COMPLEX_TRIGGER
    BEFORE INSERT OR UPDATE OR DELETE ON COMPLEX_BUSINESS_TABLE
    FOR EACH ROW
DECLARE
    -- Variable declarations
    V_TRIGGER_NAME                    CONSTANT VARCHAR2(100) := 'COMPREHENSIVE_COMPLEX_TRIGGER';
    V_USERID                          VARCHAR2(100);
    V_COUNTER                         PLS_INTEGER := 0;
    V_STATUS_CD                       VARCHAR2(2);
    V_DESCRIPTION                     VARCHAR2(500);
    V_MOLECULE_ID                     VARCHAR2(20);
    V_THEME_NO                        VARCHAR2(10);
    V_ACTION_TYPE                     VARCHAR2(20);
    V_DEBUG_MODE                      BOOLEAN := TRUE;
    V_PROCESSING_FLAG                 BOOLEAN := FALSE;
    
    -- Array/Table type declarations
    TYPE T_STRING_ARRAY IS TABLE OF VARCHAR2(100) INDEX BY PLS_INTEGER;
    V_STRING_ARRAY                    T_STRING_ARRAY;
    
    -- Record type declarations
    TYPE T_COMPANY_RECORD IS RECORD (
        COMPANY_CD                    VARCHAR2(50),
        COMPANY_NAME                  VARCHAR2(200),
        COMPANY_TYPE                  VARCHAR2(10),
        VALID_FROM                   DATE,
        STATUS_CD                    VARCHAR2(2)
    );
    V_COMPANY_REC                     T_COMPANY_RECORD;
    
    -- Cursor declarations
    CURSOR C_COMPANY_MAPPINGS IS
        SELECT COMPANY_CD, LEGAL_COMPANY_CD, REPORTING_ENTITY_CD
        FROM CFG_V_COMPANIES
        WHERE VALID_IND = 'Y' AND CBC_GBE_SCOPE = 'Y'
        ORDER BY COMPANY_CD;
    
    CURSOR C_THEME_MOLECULES IS
        SELECT MOLECULE_ID, MOLECULE_DESC, RG_NO, COMPARATOR_IND
        FROM V_THEME_MOLECULES
        WHERE VALID_IND = 'Y'
        ORDER BY MOLECULE_ID;
    
    -- Exception declarations
    ERR_INS EXCEPTION;
    ERR_DEL EXCEPTION;
    ERR_UPD EXCEPTION;
    INVALID_THEME_NO EXCEPTION;
    THEME_NO_CANNOT_BE_INSERTED EXCEPTION;
    INVALID_MOLECULE_ID EXCEPTION;
    ERR_MAP_EXISTS EXCEPTION;
    THEME_NO_ONLY_INSERT EXCEPTION;
    ERR_NOT_ALLOWED_TO_INVALIDATE EXCEPTION;
    CUSTOM_BUSINESS_RULE_EXCEPTION EXCEPTION;
    
    -- Constants
    C_MOLECULE_TYPE_ID                CONSTANT NUMBER := 99;
    C_PROPOSAL_STATUS_ACTIVE          CONSTANT VARCHAR2(1) := 'A';
    C_MAX_DESCRIPTION_LENGTH          CONSTANT PLS_INTEGER := 500;
    C_MIN_THEME_LENGTH                CONSTANT PLS_INTEGER := 4;
    C_MAX_THEME_LENGTH                CONSTANT PLS_INTEGER := 5;
    
BEGIN
    -- Initialize arrays
    V_STRING_ARRAY(1) := 'COMPANY_A';
    V_STRING_ARRAY(2) := 'COMPANY_B';
    V_STRING_ARRAY(3) := 'COMPANY_C';
    
    -- Initialize user ID with nested BEGIN-END block
    BEGIN
        V_USERID := TXO_UTIL.GET_USERID;
        IF V_USERID IS NULL THEN
            BEGIN
                V_USERID := USER;
                IF V_DEBUG_MODE THEN
                    DBMS_OUTPUT.PUT_LINE('User ID initialized to: ' || V_USERID);
                END IF;
            EXCEPTION
                WHEN OTHERS THEN
                    V_USERID := 'SYSTEM';
            END;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            V_USERID := USER;
    END;
    
    -- Determine action type with CASE statement
    CASE 
        WHEN INSERTING THEN
            V_ACTION_TYPE := 'INSERT';
            V_PROCESSING_FLAG := TRUE;
        WHEN UPDATING THEN
            V_ACTION_TYPE := 'UPDATE';
            V_PROCESSING_FLAG := TRUE;
        WHEN DELETING THEN
            V_ACTION_TYPE := 'DELETE';
            V_PROCESSING_FLAG := TRUE;
        ELSE
            V_ACTION_TYPE := 'UNKNOWN';
            V_PROCESSING_FLAG := FALSE;
    END CASE;
    
    -- Main business logic section
    IF V_PROCESSING_FLAG THEN
        
        -- INSERT logic with complex validation
        IF INSERTING THEN
            BEGIN
                -- Validate theme number format with nested CASE-WHEN
                CASE LENGTH(:NEW.THEME_NO)
                    WHEN C_MIN_THEME_LENGTH THEN
                        IF (SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9) THEN
                            RAISE INVALID_THEME_NO;
                        END IF;
                    WHEN C_MAX_THEME_LENGTH THEN
                        IF (SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9
                            OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9) THEN
                            RAISE INVALID_THEME_NO;
                        END IF;
                    ELSE
                        RAISE INVALID_THEME_NO;
                END CASE;
                
                -- Check if theme number already exists
                BEGIN
                    SELECT COUNT(*) INTO V_COUNTER
                    FROM (
                        SELECT THEME_NO FROM V_THEMES
                        UNION ALL
                        SELECT THEME_NO FROM GMD.THEMES_ARCHIVE
                    ) T
                    WHERE T.THEME_NO = :NEW.THEME_NO;
                    
                    IF V_COUNTER > 0 THEN
                        RAISE THEME_NO_CANNOT_BE_INSERTED;
                    END IF;
                EXCEPTION
                    WHEN NO_DATA_FOUND THEN
                        NULL;
                END;
                
                -- Process molecule assignment
                IF :NEW.MOLECULE_ID IS NOT NULL THEN
                    BEGIN
                        SELECT RG_NO, COMPARATOR_IND 
                        INTO V_RG_NO, V_COMPARATOR_IND
                        FROM V_THEME_MOLECULES
                        WHERE MOLECULE_ID = :NEW.MOLECULE_ID
                        AND VALID_IND = 'Y';
                        
                        IF V_RG_NO IS NULL AND V_COMPARATOR_IND = 'N' THEN
                            BEGIN
                                SELECT NEW_RG_NO INTO V_NEW_RG_NO
                                FROM (
                                    SELECT ROWNUM AS NEW_RG_NO
                                    FROM DUAL
                                    CONNECT BY 1 = 1 AND ROWNUM <= 6999
                                ) 
                                WHERE NEW_RG_NO > 5999 
                                MINUS
                                SELECT TO_NUMBER(RG_NO)
                                FROM V_THEME_MOLECULES
                                WHERE ROWNUM = 1;
                                
                                UPDATE V_THEME_MOLECULES
                                SET RG_NO = V_NEW_RG_NO
                                WHERE MOLECULE_ID = :NEW.MOLECULE_ID;
                            EXCEPTION
                                WHEN NO_DATA_FOUND THEN
                                    RAISE INVALID_MOLECULE_ID;
                            END;
                        END IF;
                    EXCEPTION
                        WHEN NO_DATA_FOUND THEN
                            RAISE INVALID_MOLECULE_ID;
                    END;
                END IF;
                
                -- Process company mappings with FOR loop
                BEGIN
                    OPEN C_COMPANY_MAPPINGS;
                    LOOP
                        FETCH C_COMPANY_MAPPINGS INTO V_COMPANY_REC.COMPANY_CD, V_COMPANY_REC.LEGAL_COMPANY_CD, V_COMPANY_REC.REPORTING_ENTITY_CD;
                        EXIT WHEN C_COMPANY_MAPPINGS%NOTFOUND;
                        
                        BEGIN
                            SELECT COUNT(*) INTO V_COUNTER
                            FROM CFG_V_COMPANIES
                            WHERE COMPANY_TYPE_CD IN ('L')
                            AND VALID_IND = 'Y'
                            AND COMPANY_CD = V_COMPANY_REC.LEGAL_COMPANY_CD;
                            
                            IF V_COUNTER = 0 THEN
                                IF V_DEBUG_MODE THEN
                                    DBMS_OUTPUT.PUT_LINE('Invalid legal company: ' || V_COMPANY_REC.LEGAL_COMPANY_CD);
                                END IF;
                            END IF;
                        EXCEPTION
                            WHEN OTHERS THEN
                                IF V_DEBUG_MODE THEN
                                    DBMS_OUTPUT.PUT_LINE('Company validation error: ' || SQLERRM);
                                END IF;
                        END;
                    END LOOP;
                    CLOSE C_COMPANY_MAPPINGS;
                EXCEPTION
                    WHEN OTHERS THEN
                        IF C_COMPANY_MAPPINGS%ISOPEN THEN
                            CLOSE C_COMPANY_MAPPINGS;
                        END IF;
                        RAISE;
                END;
                
                -- Process theme molecules with FOR loop
                BEGIN
                    OPEN C_THEME_MOLECULES;
                    LOOP
                        FETCH C_THEME_MOLECULES INTO V_MOLECULE_REC.MOLECULE_ID, V_MOLECULE_REC.MOLECULE_DESC, V_MOLECULE_REC.RG_NO, V_MOLECULE_REC.COMPARATOR_IND;
                        EXIT WHEN C_THEME_MOLECULES%NOTFOUND;
                        
                        IF V_MOLECULE_REC.COMPARATOR_IND = 'N' THEN
                            BEGIN
                                SELECT MOLECULE_TYPE_ID, PHARMACOLOGICAL_TYPE_ID 
                                INTO V_MOLECULE_TYPE_ID, V_PHARMACOLOGICAL_TYPE_ID
                                FROM V_THEME_MOLECULES
                                WHERE MOLECULE_ID = V_MOLECULE_REC.MOLECULE_ID
                                AND VALID_IND = 'Y';
                            EXCEPTION
                                WHEN NO_DATA_FOUND THEN
                                    V_MOLECULE_TYPE_ID := C_MOLECULE_TYPE_ID;
                                    V_PHARMACOLOGICAL_TYPE_ID := 19;
                            END;
                        END IF;
                    END LOOP;
                    CLOSE C_THEME_MOLECULES;
                EXCEPTION
                    WHEN OTHERS THEN
                        IF C_THEME_MOLECULES%ISOPEN THEN
                            CLOSE C_THEME_MOLECULES;
                        END IF;
                        RAISE;
                END;
                
                -- Array processing with FOR loop
                FOR i IN 1..V_STRING_ARRAY.COUNT LOOP
                    IF V_DEBUG_MODE THEN
                        DBMS_OUTPUT.PUT_LINE('Processing array element ' || i || ': ' || V_STRING_ARRAY(i));
                    END IF;
                END LOOP;
                
            EXCEPTION
                WHEN INVALID_THEME_NO THEN
                    RAISE_APPLICATION_ERROR(-20101, 'Invalid theme number format');
                WHEN THEME_NO_CANNOT_BE_INSERTED THEN
                    RAISE_APPLICATION_ERROR(-20102, 'Theme number already exists');
                WHEN INVALID_MOLECULE_ID THEN
                    RAISE_APPLICATION_ERROR(-20103, 'Invalid molecule ID');
                WHEN OTHERS THEN
                    RAISE_APPLICATION_ERROR(-20999, 'Unexpected error during insert: ' || SQLERRM);
            END;
            
        -- UPDATE logic
        ELSIF UPDATING THEN
            BEGIN
                IF :NEW.THEME_NO <> :OLD.THEME_NO THEN
                    RAISE THEME_NO_ONLY_INSERT;
                END IF;
                
                -- Process molecule mapping updates
                BEGIN
                    SELECT COUNT(*) INTO V_COUNTER
                    FROM V_THEME_MOLECULE_MAP
                    WHERE THEME_NO = :NEW.THEME_NO
                    AND MOLECULE_ID = :NEW.MOLECULE_ID
                    AND VALID_IND = 'Y';
                    
                    IF V_COUNTER > 0 THEN
                        RAISE ERR_MAP_EXISTS;
                    END IF;
                    
                    IF :NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO THEN
                        BEGIN
                            UPDATE THEME_MOLECULE_MAP
                            SET VALID_IND = 'N'
                            WHERE THEME_NO = :NEW.THEME_NO
                            AND MOLECULE_ID = :OLD.MOLECULE_ID;
                            
                            IF :OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO THEN
                                UPDATE THEME_MOLECULE_MAP
                                SET MOLECULE_SEQ_NO = MOLECULE_SEQ_NO - 1
                                WHERE THEME_NO = :NEW.THEME_NO
                                AND MOLECULE_SEQ_NO > :OLD.MOLECULE_SEQ_NO
                                AND MOLECULE_SEQ_NO <= :NEW.MOLECULE_SEQ_NO
                                AND VALID_IND = 'Y';
                            ELSE
                                UPDATE THEME_MOLECULE_MAP
                                SET MOLECULE_SEQ_NO = MOLECULE_SEQ_NO + 1
                                WHERE THEME_NO = :NEW.THEME_NO
                                AND VALID_IND = 'Y'
                                AND MOLECULE_SEQ_NO >= :NEW.MOLECULE_SEQ_NO
                                AND MOLECULE_SEQ_NO < :OLD.MOLECULE_SEQ_NO;
                            END IF;
                            
                            INSERT INTO THEME_MOLECULE_MAP (
                                THEME_NO, MOLECULE_ID, MOLECULE_SEQ_NO, 
                                MOLECULE_MAP_CHAR, VALID_IND
                            ) VALUES (
                                :NEW.THEME_NO, :NEW.MOLECULE_ID, :NEW.MOLECULE_SEQ_NO,
                                :NEW.MOLECULE_MAP_CHAR, 'Y'
                            );
                        EXCEPTION
                            WHEN OTHERS THEN
                                RAISE ERR_UPD_INV_MAP;
                        END;
                    END IF;
                EXCEPTION
                    WHEN ERR_MAP_EXISTS THEN
                        RAISE_APPLICATION_ERROR(-20110, 'Mapping already exists');
                    WHEN ERR_UPD_INV_MAP THEN
                        RAISE_APPLICATION_ERROR(-20111, 'Invalid mapping update');
                END;
                
            EXCEPTION
                WHEN THEME_NO_ONLY_INSERT THEN
                    RAISE_APPLICATION_ERROR(-20113, 'Theme number cannot be updated');
                WHEN OTHERS THEN
                    RAISE_APPLICATION_ERROR(-20998, 'Unexpected error during update: ' || SQLERRM);
            END;
            
        -- DELETE logic
        ELSIF DELETING THEN
            BEGIN
                IF NVL(:OLD.ADDRESS_TYPE_CD, 'X') IN ('L', 'P') THEN
                    RAISE ERR_NOT_ALLOWED_TO_INVALIDATE;
                END IF;
                
                BEGIN
                    UPDATE THEME_MOLECULE_MAP
                    SET VALID_IND = 'N'
                    WHERE THEME_NO = :OLD.THEME_NO
                    AND MOLECULE_ID = :OLD.MOLECULE_ID;
                    
                    UPDATE THEME_MOLECULE_MAP
                    SET MOLECULE_SEQ_NO = MOLECULE_SEQ_NO - 1
                    WHERE THEME_NO = :OLD.THEME_NO
                    AND MOLECULE_SEQ_NO > :OLD.MOLECULE_SEQ_NO
                    AND VALID_IND = 'Y';
                EXCEPTION
                    WHEN OTHERS THEN
                        RAISE ERR_DEL;
                END;
                
            EXCEPTION
                WHEN ERR_NOT_ALLOWED_TO_INVALIDATE THEN
                    RAISE_APPLICATION_ERROR(-20114, 'Not allowed to invalidate this type of record');
                WHEN ERR_DEL THEN
                    RAISE_APPLICATION_ERROR(-20115, 'Error during deletion');
            END;
        END IF;
        
        -- Final validation and cleanup
        BEGIN
            SELECT COUNT(*) INTO V_COUNTER
            FROM (
                SELECT MOLECULE_SEQ_NO
                FROM THEME_MOLECULE_MAP
                WHERE THEME_NO = NVL(:NEW.THEME_NO, :OLD.THEME_NO)
                AND VALID_IND = 'Y'
                GROUP BY MOLECULE_SEQ_NO
                HAVING COUNT(*) > 1
            );
            
            IF V_COUNTER > 0 THEN
                RAISE ERR_INV_MOL_SEQUENCE;
            END IF;
            
            -- Clean up expired records with FOR loop
            FOR EXPIRED_REC IN (
                SELECT THEME_NO, REGISTRAT_DATE
                FROM V_THEMES
                WHERE VALID_TO <= TRUNC(SYSDATE)
            ) LOOP
                DELETE FROM GMD.THEMES
                WHERE THEME_NO = EXPIRED_REC.THEME_NO
                AND REGISTRAT_DATE = EXPIRED_REC.REGISTRAT_DATE;
            END LOOP;
            
        EXCEPTION
            WHEN ERR_INV_MOL_SEQUENCE THEN
                RAISE_APPLICATION_ERROR(-20116, 'Invalid molecule sequence detected');
        END;
        
    END IF;
    
    -- Log execution
    IF V_DEBUG_MODE THEN
        DBMS_OUTPUT.PUT_LINE('Trigger execution completed: ' || V_ACTION_TYPE);
    END IF;
    
EXCEPTION
    WHEN ERR_INS THEN
        RAISE_APPLICATION_ERROR(-20117, V_TRIGGER_NAME || ' - Insert error');
    WHEN ERR_DEL THEN
        RAISE_APPLICATION_ERROR(-20118, V_TRIGGER_NAME || ' - Delete error');
    WHEN ERR_UPD THEN
        RAISE_APPLICATION_ERROR(-20119, V_TRIGGER_NAME || ' - Update error');
    WHEN CUSTOM_BUSINESS_RULE_EXCEPTION THEN
        RAISE_APPLICATION_ERROR(-20132, 'Custom business rule violation');
    WHEN OTHERS THEN
        RAISE_APPLICATION_ERROR(-20999, V_TRIGGER_NAME || ' - Unexpected error: ' || SQLERRM);
END;
/
