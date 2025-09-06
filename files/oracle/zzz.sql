DECLARE
    v_cntr    PLS_INTEGER := 0;
    err_del   EXCEPTION;
    err_upd   EXCEPTION;
    err_upd2   EXCEPTION;
BEGIN
    IF NVL(txo_util.get_userid,'GENERIC') = 'GENERIC' THEN
        RAISE err_upd;
    END IF;
    IF UPDATING AND :OLD.STATUS_CD IN ('D','A') AND :OLD.STATUS_CD = :NEW.STATUS_CD THEN
        RAISE err_upd2;
    END IF;
    IF UPDATING
    THEN
        -- FILL RECORD


        /* TO GENERATE THE COLUMN OF THE SELECT STATEMENT BELOW
        SELECT --  ALL COLUMNS
          INTO MDM_UTIL_CFG_REQUESTS.REQUEST_REC
                FROM DUAL;


        SELECT ',:NEW.'||COLUMN_NAME
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME = 'MDM_V_COMPANY_CHANGES_MTN'
        ORDER BY COLUMN_ID
        */
        SELECT :NEW.REQUEST_ID
              ,:NEW.REQUEST_TYPE_CD
              ,:NEW.CODE
              ,:NEW.REQUEST_DATE
              ,:NEW.REQUESTOR_USERID
              ,:NEW.REQUESTOR
              ,:NEW.REVIEW_DATE
              ,:NEW.REVIEW_USERID
              ,:NEW.REVIEWER
              ,:NEW.APPROVAL_DATE
              ,:NEW.APPROVAL_USERID
              ,:NEW.APPROVER
              ,:NEW.CHANGED_OBJECTS
              ,:NEW.BLANK
              ,:NEW.LAST_UPDATE
              ,:NEW.STATUS_CD
              ,:NEW.REQUEST_COMMENT
              ,:NEW.REJECT_DATE
              ,:NEW.REJECT_USERID
              ,:NEW.REJECTER
              ,:NEW.IS_CPY_OR_REN
              ,:NEW.COMMENT_NEW
        INTO mdm_util_variables.request_admin_rec
        FROM DUAL;


        mdm_util_cfg_requests.mod_request;
    END IF;
EXCEPTION
    WHEN err_upd THEN
        raise_application_error (-20101, 'MDM_V_FIN_REQUESTS_ADMIN_MTN_IOF');
    WHEN err_upd2 THEN
        raise_application_error (-20103, 'MDM_V_FIN_REQUESTS_ADMIN_MTN_IOF');
    WHEN err_del
    THEN
        raise_application_error (-20102, 'MDM_V_FIN_REQUESTS_ADMIN_MTN_IOF');
END;



