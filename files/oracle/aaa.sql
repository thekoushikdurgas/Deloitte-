DECLARE
    V_TRIGGER_NAME                    CONSTANT VARCHAR2 (30) := 'COMPANIES_MTN_IOF';
    CNTR                              PLS_INTEGER;
    ERR_INS EXCEPTION;
    ERR_DEL EXCEPTION;
    ERR_UPD EXCEPTION;
    V_USERID                          VARCHAR2 (100);
    V_REPORTING_ENTITY_CD             CFG_V_REPORTING_ENTITIES.REPORTING_ENTITY_CD%TYPE;
    V_LEGAL_COMPANY_CD                CFG_V_COMPANIES.LEGAL_COMPANY_CD%TYPE;
    V_OLD_LEGAL_COMPANY_CD            CFG_V_COMPANIES.LEGAL_COMPANY_CD%TYPE := NVL(:OLD.LEGAL_COMPANY_CD, :NEW.LEGAL_COMPANY_CD);
    V_REP_CBC_FLAG                    CFG_V_REPORTING_ENTITIES.CBC_FLAG%TYPE;
    ERR_VALID_FROM_DATE EXCEPTION;
    RU_NOT_IN_CBC_SCOPE EXCEPTION;
    ERR_NO_ADR EXCEPTION;
    ERR_CPY_STILL_IN_SCOPE EXCEPTION;
    CPY_IN_USE EXCEPTION;
    INVALID_LEGAL_COMP EXCEPTION;
    ERR_CPY_STILL_IN_MFR EXCEPTION;
    ERR_ASSOC_ENT_NOT_ALLOWED_FOR_CBC EXCEPTION;
    V_ADDR_VALID_FROM_DATE            CFG.CFG_V_COMPANY_ADDRESSES.VALID_FROM%TYPE;
    V_COUNTRY_CD                      CFG.CFG_V_COMPANY_ADDRESSES.COUNTRY_CD%TYPE;
    V_COMPANY_CODES_LIST              VARCHAR2(200);
BEGIN
    BEGIN
        V_USERID := TXO_UTIL.GET_USERID;
    EXCEPTION
        WHEN OTHERS THEN
            V_USERID := USER;
    END;

    IF UPDATING AND :OLD.COMPANY_CD != :NEW.COMPANY_CD THEN
        RAISE ERR_UPD;
    END IF;

    IF INSERTING THEN
        CNTR := 0;
 
        -- check if company_cd already exists
        SELECT
            COUNT (*) INTO CNTR
        FROM
            CFG_V_COMPANIES
        WHERE
            COMPANY_CD = :NEW.COMPANY_CD;
        IF CNTR > 0 THEN
            RAISE ERR_INS;
        END IF;
    END IF;

    IF INSERTING OR UPDATING THEN
 
        -- Fix CHG0388122 - [FIN] Companies Maintenance - Legal Entity CD
        IF :NEW.COMPANY_TYPE_CD IN ('L', 'A') AND :NEW.LEGAL_COMPANY_CD IS NULL THEN
            V_LEGAL_COMPANY_CD := :NEW.COMPANY_CD;
        ELSE
            V_LEGAL_COMPANY_CD := :NEW.LEGAL_COMPANY_CD;
        END IF;
 

        --check if the value inserted in legal company field is actually a valid legal company or a valid associate entity
        CNTR := 0;
        SELECT
            COUNT (*) INTO CNTR
        FROM
            CFG_V_COMPANIES
        WHERE
            COMPANY_TYPE_CD IN ( 'L')
            AND VALID_IND = 'Y'
            AND COMPANY_CD = V_LEGAL_COMPANY_CD;
 
        --if count is 0 then no valid legal company => return error
        IF CNTR = 0 AND (NVL(:NEW.COMPANY_TYPE_CD, :OLD.COMPANY_TYPE_CD) NOT IN ('D', 'A', 'L')
        OR (:NEW.COMPANY_TYPE_CD = 'D'
        AND :NEW.CBC_GBE_SCOPE = 'Y'
        AND V_LEGAL_COMPANY_CD <> :NEW.COMPANY_CD)) THEN --DE in CBC are allowed to use Legal Company Code
            RAISE INVALID_LEGAL_COMP;
        END IF;

        MDM_UTIL_COMPANIES.MODIFYCOMPANY (
            I_COMPANY_CD => :NEW.COMPANY_CD,
            I_COMPANY_TYPE_CD => :NEW.COMPANY_TYPE_CD,
            I_MULTISEL_COMPANY_PURPOSE => :NEW.MULTISEL_COMPANY_PURPOSE,
            I_LEGAL_COMPANY_CD => V_LEGAL_COMPANY_CD,
            I_OFFICIAL_NAME => :NEW.OFFICIAL_NAME,
            I_SHORT_NAME => :NEW.SHORT_NAME,
            I_DISCLOSURE_NAME => :NEW.DISCLOSURE_NAME,
            I_FUNCTIONAL_CURRENCY_CD => :NEW.FUNCTIONAL_CURRENCY_CD,
            I_STATUTORY_CURRENCY_CD => :NEW.STATUTORY_CURRENCY_CD,
            I_URL => :NEW.URL,
            I_PHONEBOOK_URL => :NEW.PHONEBOOK_URL,
            I_EMERGENCY_PHONE_NO => :NEW.EMERGENCY_PHONE_NO,
            I_GENERAL_PHONE_NO => :NEW.GENERAL_PHONE_NO,
            I_GENERAL_FAX_NO => :NEW.GENERAL_FAX_NO,
            I_ANNUAL_REPORT_IND => :NEW.ANNUAL_REPORT_IND,
            I_FATCA_CD => :NEW.FATCA_CD,
            I_PHARMA_NUMBER_RANGE => :NEW.PHARMA_NUMBER_RANGE,
            I_LIQUIDATION_DATE => :NEW.LIQUIDATION_DATE,
            I_SAPINST_NO => :NEW.SAPINST_NO,
            I_SAP_COMPANY_CODE_NO => :NEW.SAP_COMPANY_CODE_NO,
            I_SAP_GO_LIVE_DATE => :NEW.SAP_GO_LIVE_DATE,
            I_SAP_GROUP_CODE => :NEW.SAP_GROUP_CODE,
            I_SAP_LOCAL_COA => :NEW.SAP_LOCAL_COA,
            I_SAP_CONTROLLING_AREA => :NEW.SAP_CONTROLLING_AREA,
            I_TOP_SYSTEM_IND => :NEW.TOP_SYSTEM_IND,
            I_TOP_GO_LIVE_DATE => :NEW.TOP_GO_LIVE_DATE,
            I_TOP_REMARKS => :NEW.TOP_REMARKS,
            I_LEGAL_REMARKS => :NEW.LEGAL_REMARKS,
            I_REMARKS => :NEW.REMARKS,
            I_LOCAL_STATUTORY_ACC => :NEW.LOCAL_STATUTORY_ACC,
            I_ICFR_COMPANY_LAYER => :NEW.ICFR_COMPANY_LAYER,
            I_TRADING_PARTNER => :NEW.TRADING_PARTNER,
            I_S4_ENTITY_ID => :NEW.S4_ENTITY_ID,
            I_RCA_DISPLAY_FLAG => :NEW.RCA_DISPLAY_FLAG,
            I_CBC_GBE_SCOPE => :NEW.CBC_GBE_SCOPE -- CHG1205462 added as part of GloBE
,
            I_WEB_DISPLAY_IND => :NEW.WEB_DISPLAY_IND,
            I_HEADCOUNT_IND => :NEW.HEADCOUNT_IND,
            I_VALID_IND => :NEW.VALID_IND,
            I_CORE_REMARKS => :NEW.CORE_REMARKS,
            I_REVIEW_USERID => :NEW.REVIEW_USERID,
            I_REVIEW_EXP_DATE => :NEW.REVIEW_EXP_DATE,
            I_REQUESTER_USERID => :NEW.REQUESTER_USERID,
            I_REQUEST_DATE => :NEW.REQUEST_DATE,
            I_CHANGE_USER => V_USERID
        );
 
        -- Reporting Entity mapping
        CASE
            WHEN NVL (:OLD.REPORTING_ENTITY_CD, '-') !=
            NVL (:NEW.REPORTING_ENTITY_CD, '-')
            OR NVL (TO_DATE (:OLD.VALID_FROM_DATE, 'DD-MM-YYYY'),
            SYSDATE + 100) !=
            NVL (TO_DATE (:NEW.VALID_FROM_DATE, 'DD-MM-YYYY'),
            SYSDATE + 100)
            OR NVL (TO_DATE (:OLD.VALID_TO_DATE, 'DD-MM-YYYY'),
            SYSDATE + 100) !=
            NVL (TO_DATE (:NEW.VALID_TO_DATE, 'DD-MM-YYYY'),
            SYSDATE + 100)
            THEN
                V_REPORTING_ENTITY_CD := :NEW.REPORTING_ENTITY_CD;
                CASE
                    WHEN ( :NEW.VALID_FROM_DATE IS NULL
                    OR :NEW.VALID_FROM_DATE IS NULL)
                    THEN
                        RAISE ERR_VALID_FROM_DATE;
                    ELSE
                        NULL;
                END CASE;
                MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_MFR (
                    I_COMPANY_CD => :NEW.COMPANY_CD,
                    I_REPORTING_ENTITY_CD => :NEW.REPORTING_ENTITY_CD,
                    I_VALID_FROM_DATE => :NEW.VALID_FROM_DATE,
                    I_VALID_TO_DATE => :NEW.VALID_TO_DATE,
                    I_CHANGE_USER => V_USERID
                );
            ELSE
                NULL;
        END CASE;

        IF NVL(:NEW.VALID_IND, 'Y') = 'N' AND NVL(:OLD.VALID_IND, 'N') = 'Y' THEN
            CNTR := 0;
 
            --check if the company is used as legal company for another company
            SELECT
                COUNT (*) INTO CNTR
            FROM
                CFG_V_COMPANIES
            WHERE
                LEGAL_COMPANY_CD = :NEW.COMPANY_CD
                AND COMPANY_CD <> :NEW.COMPANY_CD
                AND VALID_IND = 'Y';
            IF CNTR > 0 THEN
                SELECT
                    LISTAGG(DISTINCT COMPANY_CD, ', ') WITHIN GROUP (ORDER BY COMPANY_CD) INTO V_COMPANY_CODES_LIST
                FROM
                    CFG_V_COMPANIES
                WHERE
                    LEGAL_COMPANY_CD = :NEW.COMPANY_CD
                    AND COMPANY_CD <> :NEW.COMPANY_CD
                    AND VALID_IND = 'Y';
                RAISE CPY_IN_USE;
            END IF;
 

            --Deactivate the addresses in case the company switches the status from Yes to No
            UPDATE CFG.CFG_COMPANY_ADDRESSES
            SET
                VALID_TO = TRUNC (
                    SYSDATE
                ) - 1
            WHERE
                COMPANY_CD = :NEW.COMPANY_CD
                AND ( VALID_TO > TRUNC(SYSDATE)
                OR VALID_TO IS NULL);
        END IF;
 

        --when switching from LE or BR to Dummy entity, deactivate all the addresses except L, P, RES and INC
        IF :OLD.COMPANY_TYPE_CD IN ('L', 'B') AND :NEW.COMPANY_TYPE_CD = 'D' THEN
            UPDATE CFG.CFG_COMPANY_ADDRESSES
            SET
                VALID_TO = TRUNC (
                    SYSDATE
                ) - 1
            WHERE
                COMPANY_CD = :NEW.COMPANY_CD
                AND ADDRESS_TYPE_CD NOT IN ('P', 'RES', 'L', 'INC')
                AND ( VALID_TO > TRUNC(SYSDATE)
                OR VALID_TO IS NULL);
        END IF;
 

        --check the CBC/GBE scope flag before invalidating the Company
        IF :NEW.CBC_GBE_SCOPE = 'Y' AND :NEW.VALID_IND = 'N' THEN
            RAISE ERR_CPY_STILL_IN_SCOPE;
        END IF;
 

        --checkf if the valid_to date for MFR mapping is filled in before trying to deactivate the company
        IF :NEW.VALID_IND = 'N' AND NVL(:NEW.REPORTING_ENTITY_CD, :OLD.REPORTING_ENTITY_CD) IS NOT NULL AND NVL(:NEW.VALID_TO_DATE, :OLD.VALID_TO_DATE) IS NULL THEN
            RAISE ERR_CPY_STILL_IN_MFR;
        END IF;
 

        --don't allow the user to set CBC scope flag to Yes for Associate Entity
        IF :NEW.COMPANY_TYPE_CD = 'A' AND :NEW.CBC_GBE_SCOPE = 'Y' THEN
            RAISE ERR_ASSOC_ENT_NOT_ALLOWED_FOR_CBC;
        END IF;
 

        --check for company type and assign the correct value
        IF NVL(:NEW.COMPANY_TYPE_CD, :OLD.COMPANY_TYPE_CD) = 'L' OR NVL(:NEW.COMPANY_TYPE_CD, :NEW.COMPANY_TYPE_CD) = 'B' THEN
            V_REPORTING_ENTITY_CD := NVL (:NEW.COMPANY_CD, :OLD.COMPANY_CD);
        ELSE
            V_REPORTING_ENTITY_CD := V_LEGAL_COMPANY_CD;
        END IF;
 

        --check if the value for reporting_entity_cd is filled in; exception when company = Dummy entity, Legal Company Code is manadatory only when CBC/GBE Scope is YES
        IF V_REPORTING_ENTITY_CD IS NOT NULL OR :NEW.COMPANY_TYPE_CD = 'D' THEN
            IF (:NEW.CBC_GBE_SCOPE = 'Y'
            AND NVL (:OLD.CBC_GBE_SCOPE, 'N') = 'N') OR (NVL(:NEW.CBC_GBE_SCOPE, :OLD.CBC_GBE_SCOPE) = 'Y'
            AND V_LEGAL_COMPANY_CD <> NVL(:OLD.LEGAL_COMPANY_CD, :NEW.LEGAL_COMPANY_CD)) THEN
                SELECT
                    CBC_FLAG INTO V_REP_CBC_FLAG
                FROM
                    CFG_V_REPORTING_ENTITIES
                WHERE
                    REPORTING_ENTITY_CD = V_LEGAL_COMPANY_CD;
 
                --check if corresponding reporting entity has cbc_flag on YES when CBC_GBE_SCOPE is set on YES
                IF NVL (V_REP_CBC_FLAG, 'N') = 'N' THEN
                    RAISE RU_NOT_IN_CBC_SCOPE;
                END IF;

                CNTR := 0;
 
                --check if the Phisical address exists - if not, throw error - used for JU mapping
                SELECT
                    COUNT (*) INTO CNTR
                FROM
                    CFG.CFG_V_COMPANY_ADDRESSES
                WHERE
                    COMPANY_CD = V_REPORTING_ENTITY_CD
                    AND ADDRESS_TYPE_CD = 'RES';
                IF CNTR = 0 THEN
                    RAISE ERR_NO_ADR;
                END IF;

                SELECT
                    VALID_FROM,
                    COUNTRY_CD INTO V_ADDR_VALID_FROM_DATE,
                    V_COUNTRY_CD
                FROM
                    CFG.CFG_V_COMPANY_ADDRESSES
                WHERE
                    COMPANY_CD = V_REPORTING_ENTITY_CD
                    AND ADDRESS_TYPE_CD = 'RES';
 
                --in case the legal company was updated with another one, the valid from of the new mapping will not be the valid from date of the RES address but today's date
                IF V_LEGAL_COMPANY_CD <> NVL(:OLD.LEGAL_COMPANY_CD, :NEW.LEGAL_COMPANY_CD) THEN
                    V_ADDR_VALID_FROM_DATE := TRUNC(SYSDATE);
                END IF;

                MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_CE_JU (
                    I_COMPANY_CD => :NEW.COMPANY_CD,
                    I_REPORTING_ENTITY_CD => V_REPORTING_ENTITY_CD,
                    I_VALID_FROM_DATE => TRUNC (SYSDATE),
                    I_VALID_TO_DATE => NULL,
                    I_CHANGE_USER => V_USERID,
                    I_MAPPING_TYPE => 'CE',
                    I_ACTION_TYPE => 'INSERT'
                );
                MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_CE_JU (
                    I_COMPANY_CD => :NEW.COMPANY_CD,
                    I_REPORTING_ENTITY_CD => 'J-'
                                             || V_COUNTRY_CD,
                    I_VALID_FROM_DATE => V_ADDR_VALID_FROM_DATE,
                    I_VALID_TO_DATE => NULL,
                    I_CHANGE_USER => V_USERID,
                    I_MAPPING_TYPE => 'JU',
                    I_ACTION_TYPE => 'INSERT'
                );
            END IF;

            IF :NEW.CBC_GBE_SCOPE = 'N' AND NVL (:OLD.CBC_GBE_SCOPE, 'Y') = 'Y' THEN
                MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_CE_JU (
                    I_COMPANY_CD => :NEW.COMPANY_CD,
                    I_VALID_FROM_DATE => NULL,
                    I_VALID_TO_DATE => TRUNC (SYSDATE),
                    I_CHANGE_USER => V_USERID,
                    I_MAPPING_TYPE => 'CE',
                    I_ACTION_TYPE => 'UPDATE'
                );
                MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_CE_JU (
                    I_COMPANY_CD => :NEW.COMPANY_CD,
                    I_VALID_FROM_DATE => NULL,
                    I_VALID_TO_DATE => TRUNC (SYSDATE),
                    I_CHANGE_USER => V_USERID,
                    I_MAPPING_TYPE => 'JU',
                    I_ACTION_TYPE => 'UPDATE'
                );
            END IF;
        END IF;
 

        --For Oficial NAME
        CASE
            WHEN (NVL (:OLD.OFFICIAL_NAME, '-') !=
            NVL (:NEW.OFFICIAL_NAME, '-'))
            AND :OLD.OFFICIAL_NAME IS NOT NULL
            THEN
                MDMAPPL.MDM_UTIL_COMPANIES.MODIFYCOMPANYNAME (
                :NEW.COMPANY_CD,
                V_LEGAL_COMPANY_CD,
                :NEW.OFFICIAL_NAME,
                V_USERID);
            ELSE
                NULL;
        END CASE;
    ELSIF DELETING THEN
        RAISE ERR_DEL;
    END IF;
EXCEPTION
    WHEN ERR_DEL THEN
        RAISE_APPLICATION_ERROR (-20110, V_TRIGGER_NAME);
    WHEN ERR_UPD THEN
        RAISE_APPLICATION_ERROR (-20111, V_TRIGGER_NAME);
    WHEN ERR_INS THEN
        RAISE_APPLICATION_ERROR (-20114, V_TRIGGER_NAME);
    WHEN ERR_VALID_FROM_DATE THEN
        RAISE_APPLICATION_ERROR ( -20122, 'Please insert : Rep. Code Assignm. Valid from Date');
    WHEN RU_NOT_IN_CBC_SCOPE THEN
        RAISE_APPLICATION_ERROR ( -20123, 'A company cannot be in CBC/GBE scope if the RU that reports it is not in CBC scope');
    WHEN ERR_CPY_STILL_IN_SCOPE THEN
        RAISE_APPLICATION_ERROR ( -20124, 'The CBC/GBE Scope must be set to No before deactivating the company');
    WHEN ERR_NO_ADR THEN
        RAISE_APPLICATION_ERROR ( -20124, 'No Physical Address found. Please insert the address before setting the CBC/GBE Scope to Yes');
    WHEN CPY_IN_USE THEN
        RAISE_APPLICATION_ERROR ( -20125, 'The Company cannot be invalidated because is still used as Legal Company for the following companies: '
                                          || V_COMPANY_CODES_LIST);
    WHEN INVALID_LEGAL_COMP THEN
        RAISE_APPLICATION_ERROR ( -20126, V_LEGAL_COMPANY_CD
                                          || ' is not a valid Legal Company Code');
    WHEN ERR_ASSOC_ENT_NOT_ALLOWED_FOR_CBC THEN
        RAISE_APPLICATION_ERROR ( -20127, 'An Associate Entity cannot be in CBC/GBE Scope!');
    WHEN ERR_CPY_STILL_IN_MFR THEN
        RAISE_APPLICATION_ERROR ( -20127, 'Please fill in Rep. Code Assignm. Valid to Date field before invalidating the company');
END;