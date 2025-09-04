CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."MDM_V_IRTT_EVENTS_KEYC_MTN_IOF" INSTEAD OF
    INSERT OR DELETE OR UPDATE ON MDMAPPL.MDM_V_IRTT_EVENTS_KEY_CONT_MTN REFERENCING NEW AS NEW OLD AS OLD
DECLARE
    ERR_EVENT_ID_REQUIRED EXCEPTION;
    ERR_DATE_FROM_AFTER_DATE_UNTIL EXCEPTION;
    ERR_DATE_RANGE_OVERLAP EXCEPTION;
    ERR_DO_NOT_MODIFY_PAST_DATA EXCEPTION;
    V_KEY_CONTACTS_LIST            IRTT_MULTIROW_REC_C;
    L_ERROR_COUNTER                PLS_INTEGER;
BEGIN
    IF (INSERTING) THEN
 
        -- Not supported!
        HTP.P('MDM_V_IRTT_EVENTS_KEYC_MTN_IOF>INSERTING not supported!');
    ELSIF (UPDATING) THEN
 
        -- Check that event exists.
        IF :NEW.EVENT_ID IS NULL THEN
            RAISE ERR_EVENT_ID_REQUIRED;
        END IF;
 

        --
        -- Extract key acounts from XML row set.
        SELECT
            IRTT_MULTIROW_REC_T( UPPER(XT.USERID), TO_DATE(XT.VALID_FROM, MDM_UTIL_IRTT.CO_DD_MM_YYYY), TO_DATE(XT.VALID_TO, MDM_UTIL_IRTT.CO_DD_MM_YYYY)) BULK COLLECT INTO V_KEY_CONTACTS_LIST
        FROM
            XMLTABLE('/rows/row' PASSING XMLTYPE(:NEW.KEY_CONTACTS_LIST) COLUMNS
 --rowno      VARCHAR2(4)  PATH 'empno',
            USERID VARCHAR2(20) PATH 'field[1]',
            VALID_FROM VARCHAR2(20) PATH 'field[2]',
            VALID_TO VARCHAR2(20) PATH 'field[3]' ) XT;
 
        --
        -- Check if user is not a Roche employee any more then valid_until must be defined!
        L_ERROR_COUNTER:= 0;
        FOR R1 IN (
            SELECT
                B.VALUE_CD       AS USER_ID,
                B.DATE_FROM      AS VALID_FROM,
                B.DATE_UNTIL     AS VALID_UNTIL,
                E.USERID,
                E.TERMINATIONDAY
            FROM
                TABLE(V_KEY_CONTACTS_LIST) B
                LEFT OUTER JOIN V_ROCHE_EMPLOYEES_ALL E
                ON E.USERID = B.                     VALUE_CD
        ) LOOP
 
            -- mdm_util_web.return_feedback_div (p_status => 'WARNING', p_message => 'r1.user_id:'||r1.user_id||', r1.userid:'||r1.userid||', r1.valid_from:'||r1.valid_from||', r1.valid_until:'||r1.valid_until);
            -- Is a valid Roche employee.
            IF (R1.USERID IS NULL) THEN
                L_ERROR_COUNTER:= L_ERROR_COUNTER + 1;
                MDM_UTIL_WEB.RETURN_FEEDBACK_DIV (
                    P_STATUS => 'ERROR',
                    P_MESSAGE => 'Key contact '
                                 ||R1.USER_ID
                                 ||' is not a valid Roche employee.'
                );
            END IF;
 

            -- Roche employee terminated for this user?
            IF (R1.TERMINATIONDAY IS NOT NULL
            AND R1.VALID_UNTIL IS NULL) THEN
                L_ERROR_COUNTER:= L_ERROR_COUNTER + 1;
                MDM_UTIL_WEB.RETURN_FEEDBACK_DIV (
                    P_STATUS => 'ERROR',
                    P_MESSAGE => 'Key contact '
                                 ||R1.USER_ID
                                 ||' was termintated '
                                 ||R1.TERMINATIONDAY
                                 ||' as Roche employee. The "<b>Valid Until</b>" date is required.'
                );
            END IF;
        END LOOP;
 

        --
        IF (L_ERROR_COUNTER > 0) THEN
            RAISE_APPLICATION_ERROR(-20000, 'Correct your input, please.');
        END IF;
 

        --
        -- raise error if date_from > date_until
        SELECT
            COUNT(1) INTO L_ERROR_COUNTER
        FROM
            TABLE(V_KEY_CONTACTS_LIST) XT
        WHERE
            XT.DATE_FROM > NVL(XT.DATE_UNTIL, XT.DATE_FROM);
 
        --
        IF L_ERROR_COUNTER > 0 THEN
            RAISE ERR_DATE_FROM_AFTER_DATE_UNTIL;
        END IF;
 

        --
        -- check records do not overlap
        SELECT
            COUNT(CHK) INTO L_ERROR_COUNTER
        FROM
            (
                SELECT
                    XT.DATE_FROM,
                    XT.DATE_UNTIL,
                    CASE
                        WHEN XT.DATE_FROM <= LAG(NVL(XT.DATE_UNTIL, XT.DATE_FROM + 1)) OVER (ORDER BY XT.DATE_FROM)
                        THEN
                            1
                    END           CHK
                FROM
                    TABLE(V_KEY_CONTACTS_LIST) XT
            );
 
        --
        IF L_ERROR_COUNTER > 0 THEN
            RAISE ERR_DATE_RANGE_OVERLAP;
        END IF;
 

        --
        -- don't allow modification of records from the past.
        SELECT
            COUNT(1) INTO L_ERROR_COUNTER
        FROM
            CFG.CFG_IRTT_EVENT_CONTACTS C
            LEFT JOIN TABLE(V_KEY_CONTACTS_LIST) XT
            ON C.USERID = XT.VALUE_CD
            AND C.VALID_FROM = XT.DATE_FROM
        WHERE
            C.EVENT_ID = :NEW.EVENT_ID
            AND C.VALID_FROM < TRUNC(SYSDATE)
            AND XT.DATE_FROM IS NULL;
 
        --
        IF L_ERROR_COUNTER > 0 THEN
            RAISE ERR_DO_NOT_MODIFY_PAST_DATA;
        END IF;
 

        --
        DELETE FROM CFG.CFG_IRTT_EVENT_CONTACTS A
        WHERE
            A.EVENT_ID = :NEW.EVENT_ID
            AND NOT EXISTS (
                SELECT
                    1
                FROM
                    TABLE(V_KEY_CONTACTS_LIST) XT
                WHERE
                    A.USERID = XT.VALUE_CD
                    AND A.VALID_FROM = XT.DATE_FROM
            );
 
        --
        MERGE INTO CFG.CFG_IRTT_EVENT_CONTACTS A USING (
            SELECT
                XT.VALUE_CD   USERID,
                XT.DATE_FROM  VALID_FROM,
                XT.DATE_UNTIL VALID_TO
            FROM
                TABLE(V_KEY_CONTACTS_LIST) XT
            WHERE
                XT.VALUE_CD IS NOT NULL
        ) B ON (A.EVENT_ID = :NEW.EVENT_ID
        AND A.USERID = B.USERID
        AND A.VALID_FROM = B.VALID_FROM) WHEN MATCHED THEN
            UPDATE
            SET
                A.VALID_TO = B.VALID_TO WHEN NOT MATCHED THEN INSERT(
                    EVENT_ID,
                    USERID,
                    VALID_FROM,
                    VALID_TO
                ) VALUES(
                    :NEW.EVENT_ID,
                    B.USERID,
                    B.VALID_FROM,
                    B.VALID_TO
                );
 
            --
            -- Maintain role for IRTT key contacts.
            MDM_UTIL_IRTT.MAINTAIN_IRTT_ROLES();
    ELSIF (DELETING) THEN
 
            -- Not supported!
            HTP.P('MDM_V_IRTT_EVENTS_KEYC_MTN_IOF>DELETING not supported!');
    END IF;
EXCEPTION
        WHEN ERR_EVENT_ID_REQUIRED THEN
            RAISE_APPLICATION_ERROR(-20101, 'MDM_V_IRTT_EVENTS_KEY_CONT_MTN');
        WHEN ERR_DATE_FROM_AFTER_DATE_UNTIL THEN
            RAISE_APPLICATION_ERROR(-20103, 'MDM_V_IRTT_EVENTS_KEY_CONT_MTN');
        WHEN ERR_DATE_RANGE_OVERLAP THEN
            RAISE_APPLICATION_ERROR(-20105, 'MDM_V_IRTT_EVENTS_KEY_CONT_MTN');
        WHEN ERR_DO_NOT_MODIFY_PAST_DATA THEN
            RAISE_APPLICATION_ERROR(-20108, 'MDM_V_IRTT_EVENTS_KEY_CONT_MTN');
END;
/

ALTER TRIGGER "MDMAPPL"."MDM_V_IRTT_EVENTS_KEYC_MTN_IOF" ENABLE;