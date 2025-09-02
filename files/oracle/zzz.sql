CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."GLOBAL_CPY_PREFIXES_IOF"
 INSTEAD OF
  INSERT OR DELETE OR UPDATE
 ON mdmappl.mdm_v_global_cpy_prefixes_mtn
REFERENCING NEW AS NEW OLD AS OLD
DECLARE
    v_trigger_name   VARCHAR2 (100) := 'GLOBAL_CPY_PREFIXES_IOF';
    err_upd          EXCEPTION;
    err_del          EXCEPTION;
BEGIN
    IF INSERTING
    THEN
        BEGIN
            INSERT INTO v_global_cpy_prefixes (gs1_comp_prefix_no
                                              ,gs1_org_country_cd
                                              ,gcp_owner_comp_cd
                                              ,gtin_alloc_type_prim_cd
                                              ,gtin_alloc_type_sec_cd
                                              ,gtin_alloc_type_ter_cd
                                              ,sscc_relevancy_ind
                                              ,global_change_id
                                              ,reason_for_change
                                              ,valid_ind)
                 VALUES (:new.gs1_comp_prefix_no
                        ,:new.gs1_org_country_cd
                        ,:new.gcp_owner_comp_cd
                        ,:new.gtin_alloc_type_prim_cd
                        ,:new.gtin_alloc_type_sec_cd
                        ,:new.gtin_alloc_type_ter_cd
                        ,:new.sscc_relevancy_ind
                        ,:new.global_change_id
                        ,:new.reason_for_change
                        ,:new.valid_ind);
        END;
    ELSIF UPDATING
    THEN
        IF :new.gs1_comp_prefix_no <> :old.gs1_comp_prefix_no
        THEN
            RAISE err_upd;
        END IF;


        UPDATE v_global_cpy_prefixes
           SET gs1_org_country_cd = :new.gs1_org_country_cd
              ,gcp_owner_comp_cd = :new.gcp_owner_comp_cd
              ,gtin_alloc_type_prim_cd = :new.gtin_alloc_type_prim_cd
              ,gtin_alloc_type_sec_cd = :new.gtin_alloc_type_sec_cd
              ,gtin_alloc_type_ter_cd = :new.gtin_alloc_type_ter_cd
              ,sscc_relevancy_ind = :new.sscc_relevancy_ind
              ,global_change_id = :new.global_change_id
              ,reason_for_change = :new.reason_for_change
              ,valid_ind = :new.valid_ind
         WHERE gs1_comp_prefix_no = :new.gs1_comp_prefix_no;
    ELSIF DELETING
    THEN
        RAISE err_del;
    END IF;
EXCEPTION
    WHEN err_upd
    THEN
        raise_application_error (-20105, v_trigger_name);
    WHEN err_del
    THEN
        raise_application_error (-20110, v_trigger_name);
END;
ALTER TRIGGER "MDMAPPL"."GLOBAL_CPY_PREFIXES_IOF" ENABLE


