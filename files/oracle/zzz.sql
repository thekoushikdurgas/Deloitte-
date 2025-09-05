CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."MDM_V_MARKET_AUTHS_ALL_IOF" 
 INSTEAD OF 
 INSERT OR UPDATE
 ON MDMAPPL.MDM_V_MARKET_AUTHS_ALL_MTN
 REFERENCING OLD AS OLD NEW AS NEW
 FOR EACH ROW 
DECLARE
    e_insert_coa        EXCEPTION;
    e_update_coa        EXCEPTION;
    e_delete_coa        EXCEPTION;
    e_matl              EXCEPTION;
    e_matl_class        EXCEPTION;
    e_matl_no           EXCEPTION;
    e_audit_comment     EXCEPTION;
    e_defined_user      EXCEPTION;
    e_changes_user      EXCEPTION;
    e_already_deleted   EXCEPTION;
    v_count             INTEGER := 0;
    v_matl_count        INTEGER := 0;
    v_record_count      INTEGER := 0;
    p_class             v_materials.class_cd%TYPE;
    p_approval_user     VARCHAR2 (30);
    p_approval_date     DATE;
    v_market_auth_no    coa.coa_market_auths.market_auth_no%TYPE;
    v_trigger_name      VARCHAR2 (30) := 'COA_V_MARKET_AUTHS_IOF';
BEGIN
    v_market_auth_no := TRIM (REPLACE ( :new.market_auth_no, CHR (9), ''));


    /*
    Exception 1bis: e_already_deleted
    first make sure, that this record has not already been deleted
    The exception e_delete_coa is otherwise raised.
    */
    IF :old.delete_flag = 'Y'
    THEN
        SELECT COUNT (mau_id)
          INTO v_record_count
          FROM coa_market_auths_his a
         WHERE a.action = 'D' AND a.mau_id = :old.mau_id;


        IF v_record_count > 0
        THEN
            RAISE e_already_deleted;
        END IF;
    END IF;


    /*
    Exception 1: e_delete_coa
    To check the audit_comment has been modified by the user when the the delete flag is set to yes.
    The exception e_delete_coa is otherwise raised.
    */
    IF :new.delete_flag = 'Y'
    THEN
        IF ( :new.audit_comment = :old.audit_comment)
        THEN
            RAISE e_delete_coa;
        END IF;
    END IF;


    /*
    Exception 2: e_matl_class
    To check the material class has been entered by the user as FIN meaningt Finished Class.
    The exception e_matl_class is otherwise raised.
    */
    BEGIN
        SELECT class_cd
          INTO p_class
          FROM v_materials
         WHERE matl_no = :new.matl_no;


        IF p_class NOT IN ('FIN')
        THEN
            RAISE e_matl_class;
        END IF;
    EXCEPTION
        WHEN NO_DATA_FOUND
        THEN
            RAISE e_matl;
    END;


    /*
   Exception 3: e_matl_no
   To check the GENISYS material number is a valid material.
   The exception e_matl_no is otherwise raised.
   */
    SELECT COUNT (*)
      INTO v_matl_count
      FROM v_materials
     WHERE matl_no = :new.matl_no                -- changed as defined in CR 244
                                 -- AND matl_open_ind = 'Y'
    ;


    IF v_matl_count = 0
    THEN
        RAISE e_matl_no;
    END IF;


    /*
    Update Statement:
    */
    IF (UPDATING)
    THEN
        /*
       Exception 4: e_update_coa
       Its important on update that the material number and the country code do not change for a specific Marketing Auhorization No.
       The exception e_update_coa is otherwise raised.
       */


        IF ( :old.matl_no <> :new.matl_no OR :new.country_id <> :old.country_id)
        THEN
            RAISE e_update_coa;
        END IF;


        /*
        Exception 5: e_audit_comment
        To check the audit_comment has been modified by the user when the approval flag  is set to yes.
        The exception e_audit_comment is otherwise raised.
        */
        IF :new.defined_ind = :old.defined_ind
        THEN
            IF :new.audit_comment IS NULL
            THEN
                RAISE e_audit_comment;
            END IF;
        END IF;


        /*
        Exception 6: e_defined_user
        To check the update user is differnt from the insert user when twhen the approval flag  is set to yes.
        The exception e_defined_user is otherwise raised.
        */
        IF     ( :new.defined_ind = 'Y' AND :old.defined_ind = 'N')
           AND (coa_security.get_userid = NVL ( :old.upd_user, :old.ins_user))
        THEN
            RAISE e_defined_user;
        END IF;


        /*
        Exception 7: e_changes_user
        To check that no changes have been made to the following parameters, when the approval flag is set to yes;


        material no
        marketing authorization number
        audit comment
        valid indicator


        The exception e_changes_user is otherwise raised.
        */
        IF     ( :new.defined_ind = 'Y' AND :old.defined_ind = 'N')
           AND (   :old.matl_no <> :new.matl_no
                OR :old.market_auth_no <> v_market_auth_no
                OR :old.audit_comment <> :new.audit_comment
                OR :old.valid_ind <> :new.valid_ind)
        THEN
            RAISE e_changes_user;
        END IF;


        /*
        Update statement for approval flag and approval date and user.
        */
        IF     ( :old.defined_ind = 'N' AND :new.defined_ind = 'Y')
           AND (coa_security.get_userid <> NVL ( :old.upd_user, :old.ins_user))
           AND (   :old.matl_no = :new.matl_no
                OR :old.market_auth_no = v_market_auth_no
                OR :old.audit_comment = :new.audit_comment
                OR :old.valid_ind = :new.valid_ind)
        THEN
            p_approval_user := coa_security.get_userid;
            p_approval_date := SYSDATE;


            UPDATE coa_market_auths
               SET defined_ind = 'Y'
                  ,def_date = SYSDATE -- CR 2124 - BUG GENERIC as value in COA_MARKET_AUTHS_HIS.DEF_USER
                  ,def_user = coa_util.get_changing_user -- mdmappl.mdm_security.get_userid -- coa_security.get_userid
             WHERE mau_id = :new.mau_id;
        ELSE
            /*
            Update statement for the following parameters;


            material number
            audit comments
            valid indicator.
            defined indicator := 'N'
            update number


            */
            UPDATE coa_market_auths
               SET country_id = :new.country_id
                  ,matl_no = :new.matl_no
                  ,market_auth_no = v_market_auth_no
                  ,audit_comment = :new.audit_comment
                  ,defined_ind = 'N'
                  ,                                 ---DECODE (:NEW.delete_flag,
                   ---            'N', 'N',
                   ---         :NEW.defined_ind),
                   valid_ind = :new.valid_ind
                  ,upd_no = NVL (upd_no, 0) + 1
                  ,def_date = NULL
                  ,def_user = NULL
             WHERE mau_id = :new.mau_id;


            /*
            Delete statement.
            */
            IF :new.delete_flag = 'Y'
            THEN
                DELETE FROM coa_market_auths
                 WHERE country_id = :new.country_id AND matl_no = :new.matl_no;
            END IF;
        END IF;
    END IF;


    /* Insert statement. */
    IF (INSERTING)
    THEN
        v_matl_count := 0;


        SELECT COUNT (*)
          INTO v_matl_count
          FROM coa_market_auths
         WHERE matl_no = :new.matl_no AND country_id = :new.country_id;


        /*
        Exception 8: e_insert_coa
        To check that teh material number and country id doesn't already exist.
        The exception e_insert_coa is otherwise raised.
        */
        IF v_matl_count = 1
        THEN
            RAISE e_insert_coa;
        END IF;


        INSERT INTO coa_market_auths (mau_id
                                     ,country_id
                                     ,matl_no
                                     ,market_auth_no
                                     ,audit_comment
                                     ,defined_ind
                                     ,valid_ind)
        VALUES ( :new.mau_id
               , :new.country_id
               , :new.matl_no
               ,v_market_auth_no
               , :new.audit_comment
               ,'N'
               , :new.valid_ind);
    END IF;
/* Exception statements with list of user friendly comments describing the error for the user. These comments are
embedded in HTML tags and are displayed in red and bold.*/
EXCEPTION
    WHEN e_insert_coa
    THEN
        raise_application_error (-20101, v_trigger_name);
    WHEN e_update_coa
    THEN
        raise_application_error (-20102, v_trigger_name);
    WHEN e_matl_class
    THEN
        raise_application_error (-20103, v_trigger_name);
    WHEN e_changes_user
    THEN
        raise_application_error (-20104, v_trigger_name);
    WHEN e_matl_no
    THEN
        raise_application_error (-20105, v_trigger_name);
    WHEN e_audit_comment
    THEN
        raise_application_error (-20106, v_trigger_name);
    WHEN e_defined_user
    THEN
        raise_application_error (-20107, v_trigger_name);
    WHEN e_delete_coa
    THEN
        raise_application_error (-20108, v_trigger_name);
    WHEN e_matl
    THEN
        raise_application_error (-20109, v_trigger_name);
    WHEN e_already_deleted
    THEN
        raise_application_error (
            -20400
           ,'This record has already been deleted and cannot be changed anymore');
END;
/
ALTER TRIGGER "MDMAPPL"."MDM_V_MARKET_AUTHS_ALL_IOF" ENABLE;



