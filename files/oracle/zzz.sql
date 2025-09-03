CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."MDM_V_PUBLIC_HOLIDAYS_MTN_IOF" INSTEAD OF
    INSERT OR DELETE OR UPDATE ON MDMAPPL.MDM_V_PUBLIC_HOLIDAYS_MTN REFERENCING NEW AS NEW OLD AS OLD
DECLARE
    ERR_INS EXCEPTION;
    ERR_UPD EXCEPTION;
    ERR_UPD2 EXCEPTION;
    ERR_UPD3 EXCEPTION;
    ERR_UPD4 EXCEPTION;
    ERR_DEL EXCEPTION;
    ERR_LEVEL EXCEPTION;
    V_HOLIDAY_DESCS     TXO_VARCHAR_COLL;
    V_COUNTRY_CODES     TXO_VARCHAR_COLL;
    V_CHK_IS_MULTIVALUE NUMBER;
    V_CHK_DISTINCT      NUMBER;
BEGIN
 
    -- v_user_level := txo_security.get_user_level(txo_library.g_auth_mode);
    --
    IF (INSERTING
    OR UPDATING) THEN
        WITH C AS (
            SELECT
                TRIM(REGEXP_SUBSTR(:NEW.HOLIDAY_NAME, '[^,]+', 1, LEVEL)) COL
            FROM
                DUAL
            CONNECT BY
                REGEXP_SUBSTR(:NEW.HOLIDAY_NAME, '[^,]+', 1, LEVEL) IS NOT NULL
        );
        SELECT
            REGEXP_SUBSTR(C.COL, '[^[]+', 1)        HOLIDAY_DESC,
            REGEXP_SUBSTR(C.COL, '[^[]+[^]]', 1, 2) COUNTRY_CD BULK COLLECT INTO V_HOLIDAY_DESCS,
            V_COUNTRY_CODES
        FROM
            C;
 
        --
        --do some checks
        SELECT
            COUNT(COUNTRY_CD),
            COUNT(COLUMN_VALUE) - COUNT(DISTINCT COLUMN_VALUE) INTO V_CHK_IS_MULTIVALUE
 --if value is >= 1 then multivalue was sent, otherwise not !
,
            V_CHK_DISTINCT
        FROM
            TABLE (V_COUNTRY_CODES)
            LEFT JOIN COUNTRIES
            ON COUNTRY_CD = COLUMN_VALUE         ;
        IF V_CHK_IS_MULTIVALUE >= 1 AND V_CHK_IS_MULTIVALUE != V_HOLIDAY_DESCS.COUNT THEN
            RAISE ERR_UPD2;
 
            --Not all descriptions have country codes
        END IF;

        IF V_CHK_DISTINCT > 0 THEN
            RAISE ERR_UPD3;
        END IF;

        IF V_CHK_IS_MULTIVALUE <= 1 THEN
            BEGIN
                MERGE INTO CFG.CFG_IRTT_HOLIDAYS A USING (
                    SELECT
                        HOLIDAY_DATE,
                        HOLIDAY_DESC,
                        GRANTED,
                        COUNTRY_CD,
                        HOLIDAY_REMARKS,
                        VALID_IND
                    FROM
                        (
                            SELECT
                                :NEW.HOLIDAY_DATE    HOLIDAY_DATE,
                                :NEW.HOLIDAY_NAME    HOLIDAY_DESC,
                                :NEW.GRANTED         GRANTED,
                                :NEW.VALID_FOR_CH    CH,
                                :NEW.VALID_FOR_USA   USA,
                                :NEW.VALID_FOR_UK    UK,
                                :NEW.VALID_FOR_FR    FR,
                                :NEW.VALID_FOR_DE    DE,
                                :NEW.VALID_FOR_JP    JP,
                                :NEW.HOLIDAY_REMARKS HOLIDAY_REMARKS
                            FROM
                                DUAL
                        )  UNPIVOT (VALID_IND FOR COUNTRY_CD IN (CH AS 'CH',
                        USA AS 'US',
                        UK AS 'GB',
                        FR AS 'FR',
                        DE AS 'DE',
                        JP AS 'JP'))
                ) B ON (A.HOLIDAY_DATE = B.HOLIDAY_DATE
                AND A.COUNTRY_CD = B.COUNTRY_CD) WHEN MATCHED THEN UPDATE SET A.GRANTED = B.GRANTED, A.VALID_IND = B.VALID_IND, A.HOLIDAY_DESC = B.HOLIDAY_DESC, A.HOLIDAY_REMARKS = B.HOLIDAY_REMARKS WHEN NOT MATCHED THEN INSERT(HOLIDAY_DATE, HOLIDAY_DESC, GRANTED, COUNTRY_CD, HOLIDAY_REMARKS, VALID_IND) VALUES(B.HOLIDAY_DATE, B.HOLIDAY_DESC, B.GRANTED, B.COUNTRY_CD, B.HOLIDAY_REMARKS, B.VALID_IND);
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE = -1407 AND INSTR(SQLERRM, '"CFG_IRTT_HOLIDAYS"."HOLIDAY_DESC"') > 0 THEN
                        RAISE ERR_INS;
                    ELSE
                        RAISE;
                    END IF;
            END;
        ELSE
            BEGIN
                MERGE INTO CFG.CFG_IRTT_HOLIDAYS A USING ( WITH HN AS (
                    SELECT
                        A.COLUMN_VALUE HOLIDAY_DESC,
                        B.COLUMN_VALUE COUNTRY_CODE
                    FROM
                        (
                            SELECT
                                COLUMN_VALUE,
                                ROWNUM       RN
                            FROM
                                TABLE(V_HOLIDAY_DESCS)
                        ) A
                        JOIN (
                            SELECT
                                COLUMN_VALUE,
                                ROWNUM       RN
                            FROM
                                TABLE(V_COUNTRY_CODES)
                        ) B
                        ON A.RN = B.RN
                )
                    SELECT
                        HOLIDAY_DATE,
                        DECODE(VALID_IND, 'N', 'N/A', HOLIDAY_DESC) HOLIDAY_DESC,
                        GRANTED,
                        COUNTRY_CD,
                        HOLIDAY_REMARKS,
                        VALID_IND
                    FROM
                        (
                            SELECT
                                :NEW.HOLIDAY_DATE    HOLIDAY_DATE,
                                :NEW.GRANTED         GRANTED,
                                :NEW.VALID_FOR_CH    CH,
                                :NEW.VALID_FOR_USA   USA,
                                :NEW.VALID_FOR_UK    UK,
                                :NEW.VALID_FOR_FR    FR,
                                :NEW.VALID_FOR_DE    DE,
                                :NEW.VALID_FOR_JP    JP,
                                :NEW.HOLIDAY_REMARKS HOLIDAY_REMARKS
                            FROM
                                DUAL
                        )  UNPIVOT (VALID_IND FOR COUNTRY_CD IN (CH AS 'CH',
                        USA AS 'US',
                        UK AS 'GB',
                        FR AS 'FR',
                        DE AS 'DE',
                        JP AS 'JP'))
                        LEFT JOIN HN
                        ON HN.COUNTRY_CODE = COUNTRY_CD
                ) B ON (A.HOLIDAY_DATE = B.HOLIDAY_DATE
                AND A.COUNTRY_CD = B.COUNTRY_CD) WHEN MATCHED THEN UPDATE SET A.GRANTED = B.GRANTED, A.VALID_IND = B.VALID_IND, A.HOLIDAY_DESC = B.HOLIDAY_DESC, A.HOLIDAY_REMARKS = B.HOLIDAY_REMARKS WHEN NOT MATCHED THEN INSERT(HOLIDAY_DATE, HOLIDAY_DESC, GRANTED, COUNTRY_CD, HOLIDAY_REMARKS, VALID_IND) VALUES(B.HOLIDAY_DATE, B.HOLIDAY_DESC, B.GRANTED, B.COUNTRY_CD, B.HOLIDAY_REMARKS, B.VALID_IND);
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE = -1407 AND INSTR(SQLERRM, '"CFG_IRTT_HOLIDAYS"."HOLIDAY_DESC"') > 0 THEN
                        RAISE ERR_UPD4;
                    ELSE
                        RAISE;
                    END IF;
            END;
        END IF;
 

        --
        -- Handle changes to GRANTED.
        IF (:NEW.GRANTED != :OLD.GRANTED) THEN
 
            -- Recreate plant events.
            MDMAPPL.MDM_UTIL_IRTT.REGENERATE_EVENT_DATES_FOR_MONTH(
                P_YEAR => EXTRACT(YEAR FROM :NEW.HOLIDAY_DATE),
                P_MONTH => EXTRACT(MONTH FROM :NEW.HOLIDAY_DATE),
                P_START_EVENT_DATE => :NEW.HOLIDAY_DATE
            );
        END IF;
    ELSIF (DELETING) THEN
        IF :OLD.HOLIDAY_DATE IS NULL THEN
            RAISE ERR_DEL;
        END IF;
        DELETE FROM CFG.CFG_IRTT_HOLIDAYS A
        WHERE
            A.HOLIDAY_DATE = :OLD.HOLIDAY_DATE;
    END IF;
EXCEPTION
 
    --WHEN err_ins
    WHEN DUP_VAL_ON_INDEX THEN
 
        --public holiday already exists
        RAISE_APPLICATION_ERROR (-20101, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_INS THEN
 
        -- Holiday name cannot be left empty.
        RAISE_APPLICATION_ERROR (-20102, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_UPD THEN
 
        -- Please don't change Holiday Date,
        RAISE_APPLICATION_ERROR (-20103, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_UPD2 THEN
 
        -- Not all descriptions have country codes.
        RAISE_APPLICATION_ERROR (-20104, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_UPD3 THEN
 
        -- Country code entered too many times in Holiday name.
        RAISE_APPLICATION_ERROR (-20105, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_UPD4 THEN
 
        -- Holiday name cannot be left empty for one country code.
        RAISE_APPLICATION_ERROR (-20106, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_DEL THEN
 
        -- Cannot delete public holiday from the past.
        RAISE_APPLICATION_ERROR (-20107, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
    WHEN ERR_LEVEL THEN
 
        -- Error level.
        RAISE_APPLICATION_ERROR (-20108, 'MDM_V_PUBLIC_HOLIDAYS_MTN_IOF');
END;
/

ALTER TRIGGER "MDMAPPL"."MDM_V_PUBLIC_HOLIDAYS_MTN_IOF" ENABLE;