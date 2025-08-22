DECLARE
    V_TRIGGER_NAME                VARCHAR2 (100) := 'COMPANY_ADDRESSES_IOF';
    CNTR                          PLS_INTEGER;
    ERR_UPD EXCEPTION;
    ERR_INS EXCEPTION;
    ERR_CTRY_CHG EXCEPTION;
    ERR_NOT_ALLOWED_TO_INVALIDATE EXCEPTION;
    V_USERID                      VARCHAR2 (100);
    TEST_ERR EXCEPTION;
    V_COUNTRY_CD                  CORE.COUNTRIES.COUNTRY_CD%TYPE;
    V_COMPANY_TYPE_CD             CFG.CFG_COMPANIES.COMPANY_TYPE_CD%TYPE;
    ERR_INS_LEGAL_ADDR EXCEPTION;
    V_VALID_FROM                  CFG.CFG_COMPANY_ADDRESSES.VALID_FROM%TYPE;
BEGIN
    BEGIN
        V_USERID := TXO_UTIL.GET_USERID;
    EXCEPTION
        WHEN OTHERS THEN
            V_USERID := USER;
    END;

    CNTR := 0;
    SELECT
        COUNT (*) INTO CNTR
    FROM
        CFG_V_COMPANY_ADDRESSES
    WHERE
        COMPANY_CD = NVL(:NEW.COMPANY_CD, :OLD.COMPANY_CD)
        AND ADDRESS_TYPE_CD = NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD);
    IF INSERTING THEN
        IF CNTR > 0 THEN
            RAISE ERR_INS;
        END IF;
    END IF;

    IF INSERTING OR UPDATING THEN
        SELECT
            COMPANY_TYPE_CD INTO V_COMPANY_TYPE_CD
        FROM
            CFG_V_COMPANIES
        WHERE
            COMPANY_CD = NVL ( :NEW.COMPANY_CD, :OLD.COMPANY_CD);
        IF V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L') THEN
            RAISE ERR_INS_LEGAL_ADDR;
        END IF;

        IF NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L') THEN
            IF NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID THEN
                RAISE ERR_CTRY_CHG;
            END IF;

            IF CNTR = 0 THEN
 
                --insert address P/L + RES/INC with valid_from date
                MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(
                    P_COMPANY_CD => :NEW.COMPANY_CD,
                    P_ADDRESS_TYPE_CD => :NEW.ADDRESS_TYPE_CD,
                    P_ADDITIONAL_NAME => :NEW.ADDITIONAL_NAME,
                    P_STREET => :NEW.STREET,
                    P_HOUSE_NO => :NEW.HOUSE_NO,
                    P_BUILDING => :NEW.BUILDING,
                    P_ADDITIONAL_INFO => :NEW.ADDITIONAL_INFO,
                    P_ZIP_CODE => :NEW.ZIP_CODE,
                    P_CITY=> :NEW.CITY,
                    P_DISTRICT_NAME => :NEW.DISTRICT_NAME,
                    P_COUNTRY_ID => :NEW.COUNTRY_ID,
                    P_LATITUDE => :NEW.LATITUDE,
                    P_LONGITUDE => :NEW.LONGITUDE,
                    P_ADDRESS_REMARK => :NEW.ADDRESS_REMARK,
                    P_VALID_FROM => :NEW.VALID_FROM,
                    P_ACTION_TYPE => 'INSERT'
                );
            ELSE
 
                --check if there are changes on the valid_from date and country => if YES, old records will be expired and new ones will be inserted
                IF NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID THEN
 
                    --update the P/L existing address with new valid_from -1
                    --update the RES/INC address with valid_to = last day of the year of valid from date
                    --insert new P/L address with new valid_from
                    --insert new RES/INC address with first day of next year of valid from date
                    MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(
                        P_COMPANY_CD => :NEW.COMPANY_CD,
                        P_ADDRESS_TYPE_CD => :NEW.ADDRESS_TYPE_CD,
                        P_ADDITIONAL_NAME => :NEW.ADDITIONAL_NAME,
                        P_STREET => :NEW.STREET,
                        P_HOUSE_NO => :NEW.HOUSE_NO,
                        P_BUILDING => :NEW.BUILDING,
                        P_ADDITIONAL_INFO => :NEW.ADDITIONAL_INFO,
                        P_ZIP_CODE => :NEW.ZIP_CODE,
                        P_CITY=> :NEW.CITY,
                        P_DISTRICT_NAME => :NEW.DISTRICT_NAME,
                        P_COUNTRY_ID => :NEW.COUNTRY_ID,
                        P_LATITUDE => :NEW.LATITUDE,
                        P_LONGITUDE => :NEW.LONGITUDE,
                        P_ADDRESS_REMARK => :NEW.ADDRESS_REMARK,
                        P_VALID_FROM => :NEW.VALID_FROM,
                        P_ACTION_TYPE => 'CTRY_CHANGE'
                    );
 
                    --particular case for Physical address - change the JU mapping for the company
                    CNTR := 0;
 
                    --looking for B/L company types which are active and have CBC scope on Yes
                    SELECT
                        COUNT(*) INTO CNTR
                    FROM
                        CFG_V_COMPANIES
                    WHERE
                        COMPANY_CD = :NEW.COMPANY_CD
                        AND VALID_IND = 'Y'
                        AND CBC_GBE_SCOPE = 'Y'
                        AND COMPANY_TYPE_CD IN ('B', 'L');
                    IF :NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0 THEN
 
                        --update existing JU-mapping with last day of the year of valid from date
                        --insert new JU mapping with first day of the next year of the valid from date
                        SELECT
                            COUNTRY_CD INTO V_COUNTRY_CD
                        FROM
                            MDM_V_COUNTRIES
                        WHERE
                            COUNTRY_ID = :NEW.COUNTRY_ID;
 
                        --check if the the day used is first day of the year
                        IF TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01' THEN
 
                            --find the first day of the current year of valid from
                            V_VALID_FROM := TO_DATE(ADD_MONTHS(TRUNC(:NEW.VALID_FROM, 'yyyy'), 10), 'dd.mm.yyyy');
                        ELSE
 
                            --find the first day of the next year of valid from
                            V_VALID_FROM := TO_DATE(ADD_MONTHS(TRUNC(:NEW.VALID_FROM, 'yyyy'), 22), 'dd.mm.yyyy');
                        END IF;

                        MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_CE_JU (
                            I_COMPANY_CD => :NEW.COMPANY_CD,
                            I_REPORTING_ENTITY_CD => 'J-'
                                                     || V_COUNTRY_CD,
                            I_VALID_FROM_DATE => V_VALID_FROM,
                            I_VALID_TO_DATE => NULL,
                            I_CHANGE_USER => V_USERID,
                            I_MAPPING_TYPE => 'JU',
                            I_ACTION_TYPE => 'INSERT'
                        );
 
                        --do the mapping changes also for all the other companies (Rep Office and Virtual) which uses this company as legal company
                        IF V_COMPANY_TYPE_CD = 'L' THEN
                            FOR V_REC IN (
                                SELECT
                                    COMPANY_CD
                                FROM
                                    CFG_V_COMPANIES
                                WHERE
                                    LEGAL_COMPANY_CD = :NEW.COMPANY_CD
                                    AND VALID_IND = 'Y'
                                    AND CBC_GBE_SCOPE = 'Y'
                                    AND COMPANY_TYPE_CD IN ('O', 'V')
                            ) LOOP
                                MDM_UTIL_COMPANIES.MODIFYCOMPANYMAPPING_CE_JU (
                                    I_COMPANY_CD => V_REC.COMPANY_CD,
                                    I_REPORTING_ENTITY_CD => 'J-'
                                                             || V_COUNTRY_CD,
                                    I_VALID_FROM_DATE => V_VALID_FROM,
                                    I_VALID_TO_DATE => NULL,
                                    I_CHANGE_USER => V_USERID,
                                    I_MAPPING_TYPE => 'JU',
                                    I_ACTION_TYPE => 'INSERT'
                                );
                            END LOOP;
                        END IF;
                    END IF;
                ELSE
 
                    --update the existing address P/L with valid_from
                    MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(
                        P_COMPANY_CD => :NEW.COMPANY_CD,
                        P_ADDRESS_TYPE_CD => :NEW.ADDRESS_TYPE_CD,
                        P_ADDITIONAL_NAME => :NEW.ADDITIONAL_NAME,
                        P_STREET => :NEW.STREET,
                        P_HOUSE_NO => :NEW.HOUSE_NO,
                        P_BUILDING => :NEW.BUILDING,
                        P_ADDITIONAL_INFO => :NEW.ADDITIONAL_INFO,
                        P_ZIP_CODE => :NEW.ZIP_CODE,
                        P_CITY=> :NEW.CITY,
                        P_DISTRICT_NAME => :NEW.DISTRICT_NAME,
                        P_COUNTRY_ID => :NEW.COUNTRY_ID,
                        P_LATITUDE => :NEW.LATITUDE,
                        P_LONGITUDE => :NEW.LONGITUDE,
                        P_ADDRESS_REMARK => :NEW.ADDRESS_REMARK,
                        P_VALID_FROM => :NEW.VALID_FROM,
                        P_ACTION_TYPE => 'UPDATE'
                    );
                END IF;
            END IF;
        END IF;

        IF NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L') THEN
            IF CNTR = 0 THEN
 
                --insert address different than P, L address type with valid_from date
                MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(
                    P_COMPANY_CD => :NEW.COMPANY_CD,
                    P_ADDRESS_TYPE_CD => :NEW.ADDRESS_TYPE_CD,
                    P_ADDITIONAL_NAME => :NEW.ADDITIONAL_NAME,
                    P_STREET => :NEW.STREET,
                    P_HOUSE_NO => :NEW.HOUSE_NO,
                    P_BUILDING => :NEW.BUILDING,
                    P_ADDITIONAL_INFO => :NEW.ADDITIONAL_INFO,
                    P_ZIP_CODE => :NEW.ZIP_CODE,
                    P_CITY=> :NEW.CITY,
                    P_DISTRICT_NAME => :NEW.DISTRICT_NAME,
                    P_COUNTRY_ID => :NEW.COUNTRY_ID,
                    P_LATITUDE => :NEW.LATITUDE,
                    P_LONGITUDE => :NEW.LONGITUDE,
                    P_ADDRESS_REMARK => :NEW.ADDRESS_REMARK,
                    P_VALID_FROM => :NEW.VALID_FROM,
                    P_ACTION_TYPE => 'INSERT'
                );
            ELSE
 
                --update address different than P, L address type with valid_from date
                MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(
                    P_COMPANY_CD => :NEW.COMPANY_CD,
                    P_ADDRESS_TYPE_CD => :NEW.ADDRESS_TYPE_CD,
                    P_ADDITIONAL_NAME => :NEW.ADDITIONAL_NAME,
                    P_STREET => :NEW.STREET,
                    P_HOUSE_NO => :NEW.HOUSE_NO,
                    P_BUILDING => :NEW.BUILDING,
                    P_ADDITIONAL_INFO => :NEW.ADDITIONAL_INFO,
                    P_ZIP_CODE => :NEW.ZIP_CODE,
                    P_CITY=> :NEW.CITY,
                    P_DISTRICT_NAME => :NEW.DISTRICT_NAME,
                    P_COUNTRY_ID => :NEW.COUNTRY_ID,
                    P_LATITUDE => :NEW.LATITUDE,
                    P_LONGITUDE => :NEW.LONGITUDE,
                    P_ADDRESS_REMARK => :NEW.ADDRESS_REMARK,
                    P_VALID_FROM => :NEW.VALID_FROM,
                    P_ACTION_TYPE => 'UPDATE'
                );
            END IF;
        END IF;
    END IF;

    IF DELETING THEN
        IF NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P') THEN
            RAISE ERR_NOT_ALLOWED_TO_INVALIDATE;
        END IF;

        MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(P_COMPANY_CD => NVL(:NEW.COMPANY_CD, :OLD.COMPANY_CD), P_ADDRESS_TYPE_CD => NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD), P_ACTION_TYPE => 'DELETE');
    END IF;
EXCEPTION
    WHEN ERR_UPD THEN
        RAISE_APPLICATION_ERROR (-20111, 'The address cannot be updated because the Address type is different. Old address type: '
                                         ||:OLD.ADDRESS_TYPE_CD
                                         ||' New address type: '
                                         ||:NEW.ADDRESS_TYPE_CD);
    WHEN ERR_INS 
    THEN
        RAISE_APPLICATION_ERROR (-20112, 'An address already exists for this Company and Address type. To modify the existing address, please use the Update button.');
    WHEN ERR_CTRY_CHG THEN
        RAISE_APPLICATION_ERROR (-20113, 'The company country modified but not the Valid From Date. Please update also the Valid From Date.');
    WHEN TEST_ERR THEN
        RAISE_APPLICATION_ERROR (-20113, 'New: '
                                         ||:NEW.COMPANY_CD
                                         ||' Old:'
                                         ||:OLD.COMPANY_CD
                                         ||'Count: '
                                         ||CNTR);
    WHEN ERR_INS_LEGAL_ADDR THEN
        RAISE_APPLICATION_ERROR (-20113, 'The legal address cannot be inserted for this type of company');
    WHEN ERR_NOT_ALLOWED_TO_INVALIDATE THEN
        RAISE_APPLICATION_ERROR (-20113, 'It is not allowed to invalidate/delete this type of address');
END;