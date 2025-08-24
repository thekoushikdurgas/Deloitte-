DECLARE
    V_TRIGGER_NAME                    CONSTANT VARCHAR2(100) := 'COMPLEX_BUSINESS_LOGIC_TRIGGER';
    V_USERID                          VARCHAR2(100);
    V_COMPANY_CD                      VARCHAR2(50);
    V_LEGAL_COMPANY_CD                VARCHAR2(50);
    V_REPORTING_ENTITY_CD             VARCHAR2(50);
    V_COUNTRY_CD                      VARCHAR2(10);
    V_VALID_FROM_DATE                 DATE;
    V_VALID_TO_DATE                   DATE;
    V_COUNTER                         PLS_INTEGER := 0;
    V_TOTAL_COUNT                     PLS_INTEGER := 0;
    V_STATUS_CD                       VARCHAR2(2);
    V_DESCRIPTION                     VARCHAR2(500);
    V_SHORT_NAME                      VARCHAR2(100);
    V_MOLECULE_ID                     VARCHAR2(20);
    V_THEME_NO                        VARCHAR2(10);
    V_PROPOSAL_ID                     NUMBER;
    V_RG_NO                           VARCHAR2(20);
    V_COMPARATOR_IND                  VARCHAR2(1);
    V_MOLECULE_TYPE_ID                NUMBER;
    V_PHARMACOLOGICAL_TYPE_ID         NUMBER;
    V_EVOLVED_NMP_CNT                 PLS_INTEGER := 0;
    V_IS_ADMIN_CNT                    SIMPLE_INTEGER := 0;
    V_SEC_MOL_CNT                     SIMPLE_INTEGER := 0;
    V_NEW_RG_NO                       VARCHAR2(20);
    V_MOLEC_IN_LIC_PRTNR              VARCHAR2(15);
    V_THEME_DESC_PROPOSAL             VARCHAR2(500);
    V_TRADEMARK_NO                    VARCHAR2(50);
    V_ODG_NO                          VARCHAR2(2);
    V_RESGRP_CD                       VARCHAR2(2);
    V_RESLIN_CD                       VARCHAR2(2);
    V_RESLIN_DESC                     VARCHAR2(60);
    V_DBA_CD                          PLS_INTEGER;
    V_PORTF_PROJ_CD                   VARCHAR2(1);
    V_D_REGISTRAT_DATE                DATE;
    V_VALID_TO                        DATE;
    V_MANUAL_SHORT_DESC               VARCHAR2(100);
 
    -- Exception declarations
    ERR_INS EXCEPTION;
    ERR_DEL EXCEPTION;
    ERR_UPD EXCEPTION;
    ERR_VALID_FROM_DATE EXCEPTION;
    ERR_NO_ADR EXCEPTION;
    ERR_CPY_STILL_IN_SCOPE EXCEPTION;
    CPY_IN_USE EXCEPTION;
    INVALID_LEGAL_COMP EXCEPTION;
    ERR_CPY_STILL_IN_MFR EXCEPTION;
    ERR_ASSOC_ENT_NOT_ALLOWED_FOR_CBC EXCEPTION;
    RU_NOT_IN_CBC_SCOPE EXCEPTION;
    INVALID_THEME_NO EXCEPTION;
    DELETE_NO_MORE_POSSIBLE EXCEPTION;
    THEME_NO_ONLY_INSERT EXCEPTION;
    DESCRIPTION_TOO_LONG EXCEPTION;
    THEME_DESC_PROPOSAL_TOO_LONG EXCEPTION;
    THEME_NO_CANNOT_BE_INSERTED EXCEPTION;
    ONLYONEOFFICIALCHANGEPERDAY EXCEPTION;
    INSERTSMUSTBEOFFICIAL EXCEPTION;
    THEMEDESCRIPTIONMANDATORY EXCEPTION;
    THEME_DESC_NOT_UNIQUE EXCEPTION;
    IN_PREP_NOT_PORTF_PROJ EXCEPTION;
    IN_PREP_NOT_CLOSED EXCEPTION;
    INVALID_MOLECULE_ID EXCEPTION;
    SEC_MOL_LIST_NOT_EMPTY EXCEPTION;
    ADMIN_UPDATE_ONLY EXCEPTION;
    PORTF_PROJ_MOL_CRE_ERR EXCEPTION;
    DEBUGGING EXCEPTION;
    ERR_MAP_EXISTS EXCEPTION;
    ERR_MOLEC_ID_MISSING EXCEPTION;
    ERR_NO_PORTF_MOLECULE_LEFT EXCEPTION;
    ERR_UPD_INV_MAP EXCEPTION;
    ERR_INS_INV_MAP EXCEPTION;
    ERR_INV_MOL_SEQUENCE EXCEPTION;
    UPDATE_UPD EXCEPTION;
    ERR_CTRY_CHG EXCEPTION;
    ERR_NOT_ALLOWED_TO_INVALIDATE EXCEPTION;
    ERR_INS_LEGAL_ADDR EXCEPTION;
    TEST_ERR EXCEPTION;
    V_NO_UPDATE_TO_EVOLVED EXCEPTION;
    V_NO_UPDATE_TERMINATED_TO_ACTIVE EXCEPTION;
    V_NO_UPDATE_EVOLVED_TO_TERMINATED EXCEPTION;
    V_EXPLORATORY_THEMENO_NOT_NULL EXCEPTION;
 
    -- Constants
    C_MOLECULE_TYPE_ID                CONSTANT NUMBER := 99;
    C_PHARMACOLOGICAL_TYPE_ID         CONSTANT NUMBER := 19;
    C_PROPOSAL_STATUS_ACTIVE          CONSTANT VARCHAR2(1) := 'A';
    C_PROPOSAL_STATUS_EVOLVED         CONSTANT VARCHAR2(1) := 'E';
    C_PROPOSAL_STATUS_TERMINATED      CONSTANT VARCHAR2(1) := 'T';
BEGIN
 
    -- Initialize user ID
    BEGIN
        V_USERID := TXO_UTIL.GET_USERID;
    EXCEPTION
        WHEN OTHERS THEN
            V_USERID := USER;
    END;
 

    -- Main business logic section
    IF INSERTING THEN
        BEGIN
 
            -- Validate theme number format
            CASE LENGTH(:NEW.THEME_NO)
                WHEN 4 THEN
                    IF (SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0
                    AND 9) THEN
                        RAISE INVALID_THEME_NO;
                    END IF;
                WHEN 5 THEN
                    IF (SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0
                    AND 9
                    OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0
                    AND 9) THEN
                        RAISE INVALID_THEME_NO;
                    END IF;
                ELSE
                    RAISE INVALID_THEME_NO;
            END CASE;
 

            -- Check if theme number already exists
            BEGIN
                SELECT
                    COUNT(*) INTO V_COUNTER
                FROM
                    (
                        SELECT
                            THEME_NO
                        FROM
                            V_THEMES
                        UNION
                        ALL
                        SELECT
                            THEME_NO
                        FROM
                            GMD.THEMES_ARCHIVE
                    ) 
                WHERE
                    T.THEME_NO = :NEW.THEME_NO;
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
                    SELECT
                        RG_NO,
                        COMPARATOR_IND INTO V_RG_NO,
                        V_COMPARATOR_IND
                    FROM
                        V_THEME_MOLECULES
                    WHERE
                        MOLECULE_ID = :NEW.MOLECULE_ID
                        AND VALID_IND = 'Y';
 
                    -- Set RG number for first assignment
                    IF V_RG_NO IS NULL AND V_COMPARATOR_IND = 'N' THEN
                        BEGIN
 
                            -- Find next available RG number
                            SELECT
                                NEW_RG_NO INTO V_NEW_RG_NO
                            FROM
                                (
                                    SELECT
                                        ROWNUM AS NEW_RG_NO
                                    FROM
                                        DUAL
                                    CONNECT BY
                                        1 = 1
                                        AND ROWNUM <= 6999
                                )                 
                            WHERE
                                NEW_RG_NO > 5999 MINUS
                                SELECT
                                    TO_NUMBER(RG_NO)
                                FROM
                                    V_THEME_MOLECULES
                                WHERE
                                    ROWNUM = 1;
 
                            -- Update molecule with new RG number
                            UPDATE V_THEME_MOLECULES
                            SET
                                RG_NO = V_NEW_RG_NO
                            WHERE
                                MOLECULE_ID = :NEW.MOLECULE_ID;
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
 

            -- Process company mappings
            BEGIN
                OPEN C_COMPANY_MAPPINGS;
                LOOP
                    FETCH C_COMPANY_MAPPINGS INTO V_COMPANY_REC;
                    EXIT WHEN C_COMPANY_MAPPINGS%NOTFOUND;
                    BEGIN
 
                        -- Validate legal company
                        SELECT
                            COUNT(*) INTO V_COUNTER
                        FROM
                            CFG_V_COMPANIES
                        WHERE
                            COMPANY_TYPE_CD IN ('L')
                            AND VALID_IND = 'Y'
                            AND COMPANY_CD = V_COMPANY_REC.LEGAL_COMPANY_CD;
                        IF V_COUNTER = 0 THEN
                            RAISE INVALID_LEGAL_COMP;
                        END IF;
 

                        -- Process address validation
                        BEGIN
                            SELECT
                                COUNT(*) INTO V_COUNTER
                            FROM
                                CFG.CFG_V_COMPANY_ADDRESSES
                            WHERE
                                COMPANY_CD = V_COMPANY_REC.REPORTING_ENTITY_CD
                                AND ADDRESS_TYPE_CD = 'RES';
                            IF V_COUNTER = 0 THEN
                                RAISE ERR_NO_ADR;
                            END IF;
 

                            -- Get address details
                            SELECT
                                VALID_FROM,
                                COUNTRY_CD INTO V_VALID_FROM_DATE,
                                V_COUNTRY_CD
                            FROM
                                CFG.CFG_V_COMPANY_ADDRESSES
                            WHERE
                                COMPANY_CD = V_COMPANY_REC.REPORTING_ENTITY_CD
                                AND ADDRESS_TYPE_CD = 'RES';
                        EXCEPTION
                            WHEN NO_DATA_FOUND THEN
                                RAISE ERR_NO_ADR;
                        END;
                    EXCEPTION
                        WHEN INVALID_LEGAL_COMP THEN
 
                            -- Log error and continue processing
                            NULL;
                        WHEN ERR_NO_ADR THEN
 
                            -- Log error and continue processing
                            NULL;
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
 

            -- Process theme molecules
            BEGIN
                OPEN C_THEME_MOLECULES;
                LOOP
                    FETCH C_THEME_MOLECULES INTO V_THEME_REC;
                    EXIT WHEN C_THEME_MOLECULES%NOTFOUND;
                    BEGIN
 
                        -- Validate molecule type
                        IF V_THEME_REC.COMPARATOR_IND = 'N' THEN
                            BEGIN
                                SELECT
                                    MOLECULE_TYPE_ID,
                                    PHARMACOLOGICAL_TYPE_ID INTO V_MOLECULE_TYPE_ID,
                                    V_PHARMACOLOGICAL_TYPE_ID
                                FROM
                                    V_THEME_MOLECULES
                                WHERE
                                    MOLECULE_ID = V_THEME_REC.MOLECULE_ID
                                    AND VALID_IND = 'Y';
                            EXCEPTION
                                WHEN NO_DATA_FOUND THEN
                                    V_MOLECULE_TYPE_ID := C_MOLECULE_TYPE_ID;
                                    V_PHARMACOLOGICAL_TYPE_ID := C_PHARMACOLOGICAL_TYPE_ID;
                            END;
                        END IF;
                    EXCEPTION
                        WHEN OTHERS THEN
 
                            -- Log error and continue processing
                            NULL;
                    END;
                END LOOP;

                CLOSE C_THEME_MOLECULES;
            EXCEPTION
                WHEN OTHERS THEN
                    IF C_THEME_MOLECULES%ISOPEN THEN
                        CLOSE C_THEME_MOLECULES;
                    END IF;

                    RAISE;
            END;
 

            -- Process address records
            BEGIN
                OPEN C_ADDRESS_RECORDS;
                LOOP
                    FETCH C_ADDRESS_RECORDS INTO V_ADDRESS_REC;
                    EXIT WHEN C_ADDRESS_RECORDS%NOTFOUND;
                    BEGIN
 
                        -- Validate country change with valid_from date
                        IF V_ADDRESS_REC.ADDRESS_TYPE_CD IN ('P', 'L') THEN
                            BEGIN
                                SELECT
                                    COUNT(*) INTO V_COUNTER
                                FROM
                                    CFG_V_COMPANY_ADDRESSES OLD_ADDR
                                WHERE
                                    OLD_ADDR.COMPANY_CD = V_ADDRESS_REC.COMPANY_CD
                                    AND OLD_ADDR.ADDRESS_TYPE_CD = V_ADDRESS_REC.ADDRESS_TYPE_CD
                                    AND OLD_ADDR.VALID_FROM = V_ADDRESS_REC.VALID_FROM
                                    AND OLD_ADDR.COUNTRY_ID <> V_ADDRESS_REC.COUNTRY_ID;
                                IF V_COUNTER > 0 THEN
                                    RAISE ERR_CTRY_CHG;
                                END IF;
                            EXCEPTION
                                WHEN NO_DATA_FOUND THEN
                                    NULL;
                            END;
                        END IF;
                    EXCEPTION
                        WHEN ERR_CTRY_CHG THEN
 
                            -- Log error and continue processing
                            NULL;
                    END;
                END LOOP;

                CLOSE C_ADDRESS_RECORDS;
            EXCEPTION
                WHEN OTHERS THEN
                    IF C_ADDRESS_RECORDS%ISOPEN THEN
                        CLOSE C_ADDRESS_RECORDS;
                    END IF;

                    RAISE;
            END;
        EXCEPTION
            WHEN INVALID_THEME_NO THEN
                RAISE_APPLICATION_ERROR(-20101, 'Invalid theme number format');
            WHEN THEME_NO_CANNOT_BE_INSERTED THEN
                RAISE_APPLICATION_ERROR(-20102, 'Theme number already exists');
            WHEN INVALID_MOLECULE_ID THEN
                RAISE_APPLICATION_ERROR(-20103, 'Invalid molecule ID');
            WHEN OTHERS THEN
                RAISE_APPLICATION_ERROR(-20999, 'Unexpected error during insert: '
                                                || SQLERRM);
        END;
    ELSIF UPDATING THEN
        BEGIN
 
            -- Validate theme number cannot be changed
            IF :NEW.THEME_NO <> :OLD.THEME_NO THEN
                RAISE THEME_NO_ONLY_INSERT;
            END IF;
 

            -- Process molecule mapping updates
            BEGIN
 
                -- Check for existing mappings
                SELECT
                    COUNT(*) INTO V_COUNTER
                FROM
                    V_THEME_MOLECULE_MAP
                WHERE
                    THEME_NO = :NEW.THEME_NO
                    AND MOLECULE_ID = :NEW.MOLECULE_ID
                    AND VALID_IND = 'Y';
                IF V_COUNTER > 0 THEN
                    RAISE ERR_MAP_EXISTS;
                END IF;
 

                -- Handle molecule sequence changes
                IF :NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO THEN
                    BEGIN
 
                        -- Invalidate old mapping
                        UPDATE THEME_MOLECULE_MAP
                        SET
                            VALID_IND = 'N'
                        WHERE
                            THEME_NO = :NEW.THEME_NO
                            AND MOLECULE_ID = :OLD.MOLECULE_ID;
 
                        -- Adjust sequence numbers
                        IF :OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO THEN
                            UPDATE THEME_MOLECULE_MAP
                            SET
                                MOLECULE_SEQ_NO = MOLECULE_SEQ_NO - 1
                            WHERE
                                THEME_NO = :NEW.THEME_NO
                                AND MOLECULE_SEQ_NO > :OLD.MOLECULE_SEQ_NO
                                AND MOLECULE_SEQ_NO <= :NEW.MOLECULE_SEQ_NO
                                AND VALID_IND = 'Y';
                        ELSE
                            UPDATE THEME_MOLECULE_MAP
                            SET
                                MOLECULE_SEQ_NO = MOLECULE_SEQ_NO + 1
                            WHERE
                                THEME_NO = :NEW.THEME_NO
                                AND VALID_IND = 'Y'
                                AND MOLECULE_SEQ_NO >= :NEW.MOLECULE_SEQ_NO
                                AND MOLECULE_SEQ_NO < :OLD.MOLECULE_SEQ_NO;
                        END IF;
 

                        -- Insert new mapping
                        INSERT INTO THEME_MOLECULE_MAP (
                            THEME_NO,
                            MOLECULE_ID,
                            MOLECULE_SEQ_NO,
                            MOLECULE_MAP_CHAR,
                            VALID_IND
                        ) VALUES (
                            :NEW.THEME_NO,
                            :NEW.MOLECULE_ID,
                            :NEW.MOLECULE_SEQ_NO,
                            :NEW.MOLECULE_MAP_CHAR,
                            'Y'
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
 

            -- Process company status changes
            BEGIN
                IF NVL(:NEW.VALID_IND, 'Y') = 'N' AND NVL(:OLD.VALID_IND, 'N') = 'Y' THEN
                    BEGIN
 
                        -- Check if company is used as legal company
                        SELECT
                            COUNT(*) INTO V_COUNTER
                        FROM
                            CFG_V_COMPANIES
                        WHERE
                            LEGAL_COMPANY_CD = :NEW.COMPANY_CD
                            AND COMPANY_CD <> :NEW.COMPANY_CD
                            AND VALID_IND = 'Y';
                        IF V_COUNTER > 0 THEN
                            RAISE CPY_IN_USE;
                        END IF;
 

                        -- Deactivate addresses
                        UPDATE CFG.CFG_COMPANY_ADDRESSES
                        SET
                            VALID_TO = TRUNC(
                                SYSDATE
                            ) - 1
                        WHERE
                            COMPANY_CD = :NEW.COMPANY_CD
                            AND (VALID_TO > TRUNC(SYSDATE)
                            OR VALID_TO IS NULL);
                    EXCEPTION
                        WHEN CPY_IN_USE THEN
                            RAISE_APPLICATION_ERROR(-20112, 'Company cannot be invalidated - still in use');
                    END;
                END IF;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE;
            END;
        EXCEPTION
            WHEN THEME_NO_ONLY_INSERT THEN
                RAISE_APPLICATION_ERROR(-20113, 'Theme number cannot be updated');
            WHEN OTHERS THEN
                RAISE_APPLICATION_ERROR(-20998, 'Unexpected error during update: '
                                                || SQLERRM);
        END;
    ELSIF DELETING THEN
        BEGIN
 
            -- Validate deletion conditions
            IF NVL(:OLD.ADDRESS_TYPE_CD, 'X') IN ('L', 'P') THEN
                RAISE ERR_NOT_ALLOWED_TO_INVALIDATE;
            END IF;
 

            -- Process molecule mapping deletion
            BEGIN
 
                -- Invalidate mapping
                UPDATE THEME_MOLECULE_MAP
                SET
                    VALID_IND = 'N'
                WHERE
                    THEME_NO = :OLD.THEME_NO
                    AND MOLECULE_ID = :OLD.MOLECULE_ID;
 
                -- Adjust sequence numbers
                UPDATE THEME_MOLECULE_MAP
                SET
                    MOLECULE_SEQ_NO = MOLECULE_SEQ_NO - 1
                WHERE
                    THEME_NO = :OLD.THEME_NO
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
 
        -- Sanity check for duplicate sequence numbers
        SELECT
            COUNT(*) INTO V_COUNTER
        FROM
            (
                SELECT
                    MOLECULE_SEQ_NO
                FROM
                    THEME_MOLECULE_MAP
                WHERE
                    THEME_NO = NVL(:NEW.THEME_NO, :OLD.THEME_NO)
                    AND VALID_IND = 'Y'
                GROUP BY
                    MOLECULE_SEQ_NO
                HAVING
                    COUNT(*) > 1
            );
        IF V_COUNTER > 0 THEN
            RAISE ERR_INV_MOL_SEQUENCE;
        END IF;
 

        -- Clean up expired records
        BEGIN
            FOR EXPIRED_REC IN (
                SELECT
                    THEME_NO,
                    REGISTRAT_DATE
                FROM
                    V_THEMES
                WHERE
                    VALID_TO <= TRUNC(SYSDATE)
            ) LOOP
                DELETE FROM GMD.THEMES
                WHERE
                    THEME_NO = EXPIRED_REC.THEME_NO
                    AND REGISTRAT_DATE = EXPIRED_REC.REGISTRAT_DATE;
            END LOOP;
        EXCEPTION
            WHEN OTHERS THEN
 
                -- Log cleanup error but don't fail the main operation
                NULL;
        END;
    EXCEPTION
        WHEN ERR_INV_MOL_SEQUENCE THEN
            RAISE_APPLICATION_ERROR(-20116, 'Invalid molecule sequence detected');
    END;
EXCEPTION
    WHEN ERR_INS THEN
        RAISE_APPLICATION_ERROR(-20117, V_TRIGGER_NAME
                                        || ' - Insert error');
    WHEN ERR_DEL THEN
        RAISE_APPLICATION_ERROR(-20118, V_TRIGGER_NAME
                                        || ' - Delete error');
    WHEN ERR_UPD THEN
        RAISE_APPLICATION_ERROR(-20119, V_TRIGGER_NAME
                                        || ' - Update error');
    WHEN ERR_VALID_FROM_DATE THEN
        RAISE_APPLICATION_ERROR(-20120, 'Please insert: Valid from Date');
    WHEN RU_NOT_IN_CBC_SCOPE THEN
        RAISE_APPLICATION_ERROR(-20121, 'A company cannot be in CBC/GBE scope if the RU that reports it is not in CBC scope');
    WHEN ERR_CPY_STILL_IN_SCOPE THEN
        RAISE_APPLICATION_ERROR(-20122, 'The CBC/GBE Scope must be set to No before deactivating the company');
    WHEN ERR_NO_ADR THEN
        RAISE_APPLICATION_ERROR(-20123, 'No Physical Address found. Please insert the address before setting the CBC/GBE Scope to Yes');
    WHEN CPY_IN_USE THEN
        RAISE_APPLICATION_ERROR(-20124, 'The Company cannot be invalidated because is still used as Legal Company');
    WHEN INVALID_LEGAL_COMP 
    AND ERR_NO_ADR THEN
        RAISE_APPLICATION_ERROR(-20125, 'Invalid Legal Company Code');
    WHEN ERR_ASSOC_ENT_NOT_ALLOWED_FOR_CBC THEN
        RAISE_APPLICATION_ERROR(-20126, 'An Associate Entity cannot be in CBC/GBE Scope!');
    WHEN ERR_CPY_STILL_IN_MFR THEN
        RAISE_APPLICATION_ERROR(-20127, 'Please fill in Valid to Date field before invalidating the company');
    WHEN ERR_CTRY_CHG THEN
        RAISE_APPLICATION_ERROR(-20128, 'The company country modified but not the Valid From Date. Please update also the Valid From Date.');
    WHEN ERR_NOT_ALLOWED_TO_INVALIDATE THEN
        RAISE_APPLICATION_ERROR(-20129, 'It is not allowed to invalidate/delete this type of record');
    WHEN ERR_INS_LEGAL_ADDR THEN
        RAISE_APPLICATION_ERROR(-20130, 'The legal address cannot be inserted for this type of company');
    WHEN TEST_ERR THEN
        RAISE_APPLICATION_ERROR(-20131, 'Test error occurred');
    WHEN OTHERS THEN
        RAISE_APPLICATION_ERROR(-20999, V_TRIGGER_NAME
                                        || ' - Unexpected error: '
                                        || SQLERRM);
END;