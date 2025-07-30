DECLARE invalid_theme_no
EXCEPTION;

delete_no_more_possible
EXCEPTION;

theme_no_only_insert
EXCEPTION;

description_too_long
EXCEPTION;

theme_desc_proposal_too_long
EXCEPTION;

theme_desc_alt_too_long
EXCEPTION;

theme_no_cannot_be_inserted
EXCEPTION;

onlyoneofficialchangeperday
EXCEPTION;

insertsmustbeofficial
EXCEPTION;

themedescriptionmandatory
EXCEPTION;

theme_desc_not_unique
EXCEPTION;

in_prep_not_portf_proj
EXCEPTION;

in_prep_not_closed
EXCEPTION;

invalid_molecule_id
EXCEPTION;

sec_mol_list_not_empty
EXCEPTION;

admin_update_only
EXCEPTION;

portf_proj_mol_cre_err
EXCEPTION;

debugging
EXCEPTION;

v_counter pls_integer;

v_code varchar2(2);

v_odg_no varchar2(2);

v_resgrp_cd varchar2(2);

v_reslin_cd varchar2(2);

v_status_cd varchar2(1);

v_dba_cd pls_integer;

v_portf_proj_cd varchar2(1);

v_description varchar2(500);

v_reslin_desc varchar2(60);

v_theme_desc_length pls_integer;

v_d_registrat_date date;

v_d_ins_date date;

v_future_registrat date;

v_valid_to date;

v_userid varchar2(30);

v_is_admin_cnt simple_integer := 0;

v_sec_mol_cnt simple_integer := 0;

v_molecule_id varchar2(5) := NULL;

v_molecule_rg_no varchar2(20) := NULL;

v_molec_in_lic_prtnr varchar2(15) := NULL;

v_new_rg_no v_theme_molecules.rg_no%TYPE;

v_comparator_ind v_theme_molecules.comparator_ind%TYPE;

v_theme_desc_proposal mdm_v_themes_mtn.theme_desc_proposal%TYPE;

v_short_name varchar2(30);

c_molecule_type_id constant v_molecule_types.molecule_type_id%TYPE := 99;

c_pharmacological_type_id constant v_pharmacological_types.pharmacological_type_id%TYPE := 19;

v_evolved_nmp_cnt PLS_INTEGER;

v_trademark_no v_themes.trademark_no%TYPE;

v_molecule_type_id v_molecule_types.molecule_type_id%TYPE;

v_pharmacological_type_id v_pharmacological_types.pharmacological_type_id%TYPE;

BEGIN
SELECT nvl(txo_security.get_userid, USER) INTO v_userid
FROM dual;


SELECT count(*) INTO v_is_admin_cnt
FROM txo_users_roles_map
WHERE role_id IN (315)
    AND userid = v_userid;


SELECT new_rg_no INTO v_new_rg_no
FROM
    (SELECT new_rg_no
     FROM
         (SELECT rownum AS new_rg_no
          FROM dual CONNECT BY 1 = 1
          AND rownum <= 6999)
     WHERE new_rg_no > 5999 MINUS
         SELECT to_number(rg_no)
         FROM v_theme_molecules)
WHERE rownum = 1;

IF (:new.in_prep_ind = 'Y') THEN IF (:new.portf_proj_cd <> 'Y') THEN RAISE in_prep_not_portf_proj;

END IF;

IF (:new.status_desc <> 'CLOSED'
    AND v_is_admin_cnt = 0) THEN RAISE in_prep_not_closed;

END IF;

IF (:new.molecule_id IS NULL) THEN txo_util.set_warning('No Molecule assigned to In-Prep Theme ' || :new.theme_no || '!');

END IF;

END IF;

IF (:new.molecule_id IS NOT NULL) THEN BEGIN
SELECT rg_no ,
       m.comparator_ind INTO v_molecule_rg_no ,
                             v_comparator_ind
FROM v_theme_molecules m
WHERE molecule_id = :new.molecule_id
    AND m.valid_ind = 'Y';


EXCEPTION WHEN no_data_found THEN RAISE invalid_molecule_id;

END;

IF (v_molecule_rg_no IS NULL) THEN IF (v_comparator_ind = 'Y') THEN NULL;

ELSE
UPDATE v_theme_molecules
SET rg_no = v_new_rg_no
WHERE molecule_id = :new.molecule_id;

END IF;

END IF;

END IF;

v_odg_no := substr(:new.reslin_desc_concat, 1, 2);

v_resgrp_cd := substr(:new.reslin_desc_concat, 4, 2);

v_reslin_cd := substr(:new.reslin_desc_concat, 7, 2);

v_reslin_desc := substr(:new.reslin_desc_concat, 12, length(:new.reslin_desc_concat));

IF (:new.status_desc IS NOT NULL) THEN
SELECT status_cd INTO v_status_cd
FROM mdm_v_theme_status
WHERE state_desc = :new.status_desc;

ELSE v_status_cd := NULL;

END IF;

IF (:new.dba_desc_concat IS NOT NULL) THEN
SELECT dba_cd INTO v_dba_cd
FROM mdm_v_disease_biology_areas
WHERE dba_short_desc || ' - ' || dba_desc = :new.dba_desc_concat;

ELSE v_dba_cd := NULL;

END IF;

v_molec_in_lic_prtnr := gmd_util_themes.get_molec_in_lic_prtnr(:new.molecule_id);

IF (:new.official_ind = 'N') THEN v_trademark_no := :new.trademark_no;

ELSE v_trademark_no := :old.trademark_no;

END IF;

v_theme_desc_proposal := gmd_util_themes.get_theme_short_name(p_theme_no_portf => :new.theme_no, p_molecule_id_portf => :new.molecule_id, p_prod_short_cd_portf => :new.prod_short_cd, p_odg_no_port => v_odg_no, p_resgrp_cd_port => v_resgrp_cd, p_reslin_cd_port => v_reslin_cd, p_line_ext_info_port => :new.line_ext_info, p_in_lic_prtnr_portf => NULL, p_trademark_no_portf => v_trademark_no, p_trunc_desc_length => 'N');

IF (:new.manual_short_desc IS NULL
    AND length(v_theme_desc_proposal) > 30) THEN RAISE theme_desc_proposal_too_long;

END IF;

v_short_name := coalesce(:new.manual_short_desc, v_theme_desc_proposal);

IF (inserting) THEN IF (:new.in_prep_ind = 'N'
                        AND v_is_admin_cnt = 0) THEN RAISE admin_update_only;

END IF;

v_molecule_id := :new.molecule_id;

IF (:new.portf_proj_cd = 'Y'
    AND :new.molecule_id IS NULL) THEN IF (nvl(:new.manual_short_desc, :new.theme_desc_proposal) IS NULL) THEN RAISE portf_proj_mol_cre_err;

ELSE
INSERT INTO mdm_v_theme_molecules_mtn(molecule_desc , valid_ind , rg_no , cancer_immunotherapy_ind , molecule_type_id , pharmacological_type_id)
VALUES (nvl(:new.manual_short_desc, :new.theme_desc_proposal) , 'Y' , v_new_rg_no , 'N' , c_molecule_type_id , c_pharmacological_type_id);


SELECT molecule_id INTO v_molecule_id
FROM v_theme_molecules
WHERE molecule_desc = nvl(:new.manual_short_desc, :new.theme_desc_proposal)
    AND valid_ind = 'Y'
    AND rg_no = v_new_rg_no
    AND cancer_immunotherapy_ind = 'N'
    AND molecule_type_id = c_molecule_type_id
    AND pharmacological_type_id = c_pharmacological_type_id;


INSERT INTO theme_molecule_map tmmap(tmmap.theme_no , tmmap.molecule_id , tmmap.molecule_seq_no , tmmap.valid_ind)
VALUES (:new.theme_no, v_molecule_id, 1, 'Y');

END IF;

END IF;

CASE length(:new.theme_no) WHEN 4 THEN IF (substr(:new.theme_no, 1, 1) NOT BETWEEN 0 AND 9
                                           OR substr(:new.theme_no, 2, 1) NOT BETWEEN 0 AND 9
                                           OR substr(:new.theme_no, 3, 1) NOT BETWEEN 0 AND 9
                                           OR substr(:new.theme_no, 4, 1) NOT BETWEEN 0 AND 9) THEN RAISE invalid_theme_no;

END IF;

WHEN 5 THEN IF (substr(:new.theme_no, 1, 1) NOT BETWEEN 0 AND 9
                OR substr(:new.theme_no, 2, 1) NOT BETWEEN 0 AND 9
                OR substr(:new.theme_no, 3, 1) NOT BETWEEN 0 AND 9
                OR substr(:new.theme_no, 4, 1) NOT BETWEEN 0 AND 9
                OR substr(:new.theme_no, 5, 1) NOT BETWEEN 0 AND 9) THEN RAISE invalid_theme_no;

END IF;

ELSE RAISE invalid_theme_no;

END CASE;

v_counter := NULL;


SELECT count(t.theme_no) INTO v_counter
FROM
    (SELECT theme_no
     FROM v_themes
     UNION ALL SELECT theme_no
     FROM gmd.themes_archive) t
WHERE t.theme_no = :new.theme_no;

IF (v_counter > 0) THEN RAISE theme_no_cannot_be_inserted;

END IF;

v_counter := NULL;

v_d_registrat_date := sysdate;

IF (:new.official_ind = 'N') THEN RAISE insertsmustbeofficial;

END IF;

IF (upper(:new.portf_proj_cd) = 'N') THEN IF (:new.theme_desc IS NULL
                                              OR length(:new.theme_desc) = 0) THEN RAISE themedescriptionmandatory;

END IF;

END IF;

IF (upper(:new.portf_proj_cd) = 'Y') THEN v_description := gmd.gmd_util_themes.get_theme_desc_portfolio(p_theme_no_portf => NULL , p_molecule_id_portf => v_molecule_id , p_prod_short_cd_portf => :new.prod_short_cd , p_odg_no_port => v_odg_no , p_resgrp_cd_port => v_resgrp_cd , p_reslin_cd_port => v_reslin_cd , p_line_ext_info_port => :new.line_ext_info , p_in_lic_prtnr_portf => v_molec_in_lic_prtnr , p_trademark_no_portf => :new.trademark_no , p_short_name_portf => :new.short_name , p_trunc_desc_length => 'N');

IF (length(v_description) > 90) THEN RAISE description_too_long;

END IF;

v_description := trim(v_description);

v_portf_proj_cd := 'Y';

ELSE v_description := :new.theme_desc;

v_portf_proj_cd := 'N';

END IF;

v_counter := NULL;


SELECT count(t.theme_no) INTO v_counter
FROM v_themes t
WHERE t.theme_desc = v_description;

IF (v_counter > 0) THEN RAISE theme_desc_not_unique;

END IF;

v_counter := NULL;

v_valid_to := to_date('09.09.9999', 'DD.MM.YYYY');

v_short_name := nvl(:new.manual_short_desc, substr(v_description, 1, 30));


INSERT INTO gmd.themes(theme_no , registrat_date , odg_no , resgrp_cd , reslin_cd , theme_desc , short_name , status_cd , dba_cd , in_prep_ind , prod_short_cd , trademark_no , bio_activity , applicant , contact , registrar , line_ext_info , portf_proj_cd , co_dev_prtnr , technology_prtnr , official_ind , co_mar_prtnr , valid_to , portf_da_group_id , manual_short_desc)
VALUES (:new.theme_no , v_d_registrat_date , v_odg_no , v_resgrp_cd , v_reslin_cd , v_description , v_short_name , v_status_cd , v_dba_cd , :new.in_prep_ind , :new.prod_short_cd , :new.trademark_no , :new.bio_activity , :new.applicant , :new.contact , txo_util.get_userid , :new.line_ext_info , v_portf_proj_cd , :new.co_dev_prtnr , :new.technology_prtnr , :new.official_ind , :new.co_mar_prtnr , v_valid_to , :new.portf_da_group_id , :new.manual_short_desc);

IF (:old.molecule_id IS NULL
    AND :new.molecule_id IS NOT NULL) THEN
INSERT INTO mdm_v_theme_molecule_map_mtn a(a.theme_no , a.molecule_id , a.molecule_seq_no , a.valid_ind)
VALUES (:new.theme_no, v_molecule_id, 1, 'Y');

END IF;

ELSIF (updating) THEN IF (:old.in_prep_ind = 'N' or(:old.in_prep_ind = 'Y'
                                                    AND:new.in_prep_ind = 'N'))
AND v_is_admin_cnt = 0 THEN RAISE admin_update_only;

END IF;

IF (:new.theme_no <> :old.theme_no) THEN RAISE theme_no_only_insert;

END IF;

IF (:new.official_ind = 'N') THEN v_d_registrat_date := to_date(:old.registrat_date, 'dd-mm-yyyy');

ELSE v_d_registrat_date := sysdate;

END IF;

IF (upper(:new.portf_proj_cd) = 'Y' and(v_status_cd <> 'C'
                                        OR:new.in_prep_ind = 'Y')) THEN v_description := gmd.gmd_util_themes.get_theme_desc_portfolio(p_theme_no_portf => :new.theme_no , p_molecule_id_portf => :new.molecule_id , p_prod_short_cd_portf => :new.prod_short_cd , p_odg_no_port => v_odg_no , p_resgrp_cd_port => v_resgrp_cd , p_reslin_cd_port => v_reslin_cd , p_line_ext_info_port => :new.line_ext_info , p_in_lic_prtnr_portf => v_molec_in_lic_prtnr , p_trademark_no_portf => :new.trademark_no , p_short_name_portf => :new.short_name , p_trunc_desc_length => 'N');

v_description := trim(v_description);

v_portf_proj_cd := 'Y';

ELSE IF (:new.theme_desc IS NULL
         OR length(:new.theme_desc) = 0) THEN RAISE themedescriptionmandatory;

ELSE v_description := :new.theme_desc;

v_portf_proj_cd := :new.portf_proj_cd;

END IF;

END IF;

IF (length(v_description) > 90) THEN RAISE description_too_long;

END IF;

v_counter := NULL;


SELECT count(t.theme_no) INTO v_counter
FROM v_themes t
WHERE t.theme_desc = v_description
    AND t.theme_no <> :new.theme_no;

IF (v_counter > 0) THEN RAISE theme_desc_not_unique;

END IF;

v_counter := NULL;

IF (:new.official_ind = 'N') THEN
UPDATE gmd.themes
SET odg_no = v_odg_no ,
    resgrp_cd = v_resgrp_cd ,
    reslin_cd = v_reslin_cd ,
    theme_desc = v_description ,
    short_name = v_short_name ,
    status_cd = v_status_cd ,
    dba_cd = v_dba_cd ,
    in_prep_ind = :new.in_prep_ind ,
                       prod_short_cd = :new.prod_short_cd ,
                                            trademark_no = :new.trademark_no ,
                                                                bio_activity = :new.bio_activity ,
                                                                                    applicant = :new.applicant ,
                                                                                                     contact = :new.contact ,
                                                                                                                    line_ext_info = :new.line_ext_info ,
                                                                                                                                         portf_proj_cd = v_portf_proj_cd ,
                                                                                                                                         co_dev_prtnr = :new.co_dev_prtnr ,
                                                                                                                                                             technology_prtnr = :new.technology_prtnr ,
                                                                                                                                                                                     official_ind = :new.official_ind ,
                                                                                                                                                                                                         co_mar_prtnr = :new.co_mar_prtnr ,
                                                                                                                                                                                                                             portf_da_group_id = :new.portf_da_group_id ,
                                                                                                                                                                                                                                                      manual_short_desc = :new.manual_short_desc
WHERE theme_no = :new.theme_no
    AND to_date(registrat_date, 'DD-MM-YYYY') = v_d_registrat_date;

ELSE v_counter := NULL;


SELECT count(*) INTO v_counter
FROM v_themes t
WHERE trunc(t.registrat_date) = trunc(sysdate)
    AND t.theme_no = :new.theme_no;

IF (v_counter > 0) THEN RAISE onlyoneofficialchangeperday;

END IF;

v_counter := NULL;


UPDATE gmd.themes
SET odg_no = v_odg_no ,
    resgrp_cd = v_resgrp_cd ,
    reslin_cd = v_reslin_cd ,
    theme_desc = v_description ,
    short_name = v_short_name ,
    status_cd = v_status_cd ,
    dba_cd = v_dba_cd ,
    in_prep_ind = :new.in_prep_ind ,
                       prod_short_cd = :new.prod_short_cd ,
                                            trademark_no = :new.trademark_no ,
                                                                bio_activity = :new.bio_activity ,
                                                                                    applicant = :new.applicant ,
                                                                                                     contact = :new.contact ,
                                                                                                                    line_ext_info = :new.line_ext_info ,
                                                                                                                                         portf_proj_cd = v_portf_proj_cd ,
                                                                                                                                         co_dev_prtnr = :new.co_dev_prtnr ,
                                                                                                                                                             technology_prtnr = :new.technology_prtnr ,
                                                                                                                                                                                     official_ind = :new.official_ind ,
                                                                                                                                                                                                         co_mar_prtnr = :new.co_mar_prtnr ,
                                                                                                                                                                                                                             registrat_date = sysdate ,
                                                                                                                                                                                                                             registrar = v_userid ,
                                                                                                                                                                                                                             portf_da_group_id = :new.portf_da_group_id ,
                                                                                                                                                                                                                                                      manual_short_desc = :new.manual_short_desc
WHERE theme_no = :new.theme_no;

END IF;

CASE WHEN :old.molecule_id IS NULL
AND :new.molecule_id IS NOT NULL THEN
INSERT INTO mdm_v_theme_molecule_map_mtn a(a.theme_no , a.molecule_id , a.molecule_seq_no , a.valid_ind)
VALUES (:new.theme_no, :new.molecule_id, 1, 'Y');

WHEN :old.molecule_id IS NOT NULL
AND :new.molecule_id IS NOT NULL THEN
UPDATE mdm_v_theme_molecule_map a
SET a.molecule_id = :new.molecule_id,
                         a.valid_ind = 'Y'
WHERE a.theme_no = :new.theme_no
    AND a.molecule_seq_no = 1
    AND a.valid_ind = 'Y';

WHEN :old.molecule_id IS NOT NULL
AND :new.molecule_id IS NULL THEN
SELECT count(*) INTO v_sec_mol_cnt
FROM mdm_v_theme_molecule_map_mtn a
WHERE a.theme_no = :new.theme_no
    AND a.molecule_seq_no > 1
    AND a.valid_ind = 'Y';

IF (v_sec_mol_cnt > 0) THEN RAISE sec_mol_list_not_empty;

ELSE
UPDATE mdm_v_theme_molecule_map a
SET a.valid_ind = 'N'
WHERE a.molecule_id = :old.molecule_id
    AND a.theme_no = :new.theme_no
    AND a.molecule_seq_no = 1
    AND a.valid_ind = 'Y';

END IF;

ELSE NULL;

END CASE;

ELSIF (deleting) THEN IF ((:old.in_prep_ind = 'N')
                          AND v_is_admin_cnt = 0) THEN RAISE admin_update_only;

END IF;

IF (trunc(to_date(:old.registrat_date, 'DD-MM-YYYY')) = trunc(sysdate)) THEN
DELETE
FROM gmd.themes a
WHERE a.theme_no = :old.theme_no
    AND trunc(a.registrat_date) = trunc(sysdate);

ELSE RAISE delete_no_more_possible;

END IF;

END IF;

IF (inserting
    OR updating) THEN IF (:new.proposal_id IS NOT NULL
                          AND :old.proposal_id IS NULL) THEN
SELECT count(*) INTO v_evolved_nmp_cnt
FROM mdm_v_new_medicine_proposals_mtn
WHERE proposal_id = :new.proposal_id
    AND proposal_status_cd = 'E' ;

IF (v_evolved_nmp_cnt = 0) THEN
UPDATE mdm_v_new_medicine_proposals_mtn
SET proposal_status_cd = 'E',
    evolved_theme_no = :new.theme_no,
                            proposal_name = v_short_name,
                            reason_for_change = '** Automatic update of proposal_name after short_name change in evolved theme **'
WHERE proposal_id = :new.proposal_id;

END IF;

ELSE IF (:new.proposal_id IS NULL
         AND :old.proposal_id IS NOT NULL) THEN
UPDATE mdm_v_new_medicine_proposals_mtn
SET proposal_status_cd = 'A',
    evolved_theme_no = NULL
WHERE proposal_id = :old.proposal_id;

ELSE IF (:new.proposal_id IS NOT NULL
         AND :old.proposal_id IS NOT NULL
         AND :new.proposal_id <> :old.proposal_id) THEN
UPDATE mdm_v_new_medicine_proposals_mtn
SET proposal_status_cd = 'A',
    evolved_theme_no = NULL
WHERE proposal_id = :old.proposal_id;


UPDATE mdm_v_new_medicine_proposals_mtn
SET proposal_status_cd = 'E',
    evolved_theme_no = :new.theme_no,
                            proposal_name = v_short_name,
                            reason_for_change = '** Automatic update of proposal_name after short_name change in evolved theme **'
WHERE proposal_id = :new.proposal_id;

END IF;

END IF;

END IF;

IF (nvl(:new.proposal_id, 0) = nvl(:old.proposal_id, 0)
    AND nvl(:old.short_name, '-') <> nvl(v_short_name, '-')) THEN
SELECT count(*) INTO v_evolved_nmp_cnt
FROM mdm_v_new_medicine_proposals_mtn nmp
WHERE nmp.evolved_theme_no =:new.theme_no
    AND nmp.proposal_status_cd = 'E' ;

IF (v_evolved_nmp_cnt > 0) THEN
UPDATE mdm_v_new_medicine_proposals_mtn nmp
SET nmp.proposal_name = v_short_name,
    nmp.reason_for_change = '** Automatic update of proposal_name after short_name change in evolved theme **'
WHERE nmp.evolved_theme_no =:new.theme_no
    AND nmp.proposal_status_cd = 'E' ;

END IF;

END IF;

END IF;

IF (inserting
    AND :new.theme_no IS NOT NULL
    AND gmd_util_themes.get_themes_range_automatic_nmp(:new.theme_no) = 'Y') THEN IF (:new.proposal_id IS NOT NULL) THEN
SELECT count(*) INTO v_evolved_nmp_cnt
FROM mdm_v_new_medicine_proposals_mtn
WHERE proposal_id = :new.proposal_id
    AND proposal_name = v_short_name
    AND proposal_status_cd = 'E' ;

END IF;

IF (:new.proposal_id IS NULL
    OR (:new.proposal_id IS NOT NULL
        AND v_evolved_nmp_cnt = 0)) THEN IF (:new.molecule_id IS NOT NULL) THEN BEGIN
SELECT pharmacological_type_id ,
       molecule_type_id INTO v_pharmacological_type_id ,
                             v_molecule_type_id
FROM v_theme_molecules m
WHERE molecule_id = :new.molecule_id
    AND m.valid_ind = 'Y';


EXCEPTION WHEN no_data_found THEN RAISE invalid_molecule_id;

END;

END IF;


INSERT INTO mdm_v_new_medicine_proposals_mtn (proposal_status_cd, evolved_theme_no, proposal_name, pharmacological_type_id, molecule_type_id, reason_for_change)
VALUES ('E', :new.theme_no, v_short_name, nvl(v_pharmacological_type_id, c_pharmacological_type_id), nvl(v_molecule_type_id, c_molecule_type_id), '** Automatic creation of nmp for early development themes **');

END IF;

END IF;

BEGIN
FOR i1 IN
    (SELECT a.theme_no ,
            a.registrat_date
     FROM v_themes a
     WHERE a.valid_to <= trunc(sysdate)) LOOP
DELETE
FROM gmd.themes
WHERE theme_no = i1.theme_no
    AND registrat_date = i1.registrat_date;

END LOOP;

END;


EXCEPTION WHEN admin_update_only THEN raise_application_error(-20115, 'MDM_V_THEMES_IOF');

WHEN in_prep_not_portf_proj THEN raise_application_error(-20116, 'MDM_V_THEMES_IOF');

WHEN in_prep_not_closed THEN raise_application_error(-20117, 'MDM_V_THEMES_IOF');

WHEN invalid_molecule_id THEN raise_application_error(-20118, 'This is not a valid Molecule ID');

WHEN sec_mol_list_not_empty THEN raise_application_error(-20119, 'MDM_V_THEMES_IOF');

WHEN invalid_theme_no THEN raise_application_error(-20101, 'This is not a valid Theme No');

WHEN delete_no_more_possible THEN raise_application_error(-20400 , 'Theme cannot be deleted when the deletion is not on the same day, on which the Theme has been inserted');

WHEN theme_no_only_insert THEN raise_application_error(-20400, 'Theme No cannot be updated');

WHEN description_too_long THEN raise_application_error(-20400 , 'The automatically generated Theme Description "' || v_description || '" is too long');

WHEN theme_desc_proposal_too_long THEN raise_application_error(-20400 , 'The automatically generated Short Description Proposal "' || :old.theme_desc_proposal || '" is too long');

WHEN theme_desc_alt_too_long THEN raise_application_error(-20400 , 'The automatically generated Downstream Theme Description "' || :old.theme_desc_alt || '" is too long');

WHEN theme_no_cannot_be_inserted THEN raise_application_error(-20400, 'This Theme No already exists');

WHEN onlyoneofficialchangeperday THEN raise_application_error(-20400, 'Official Change for this Theme No and Day already exists');

WHEN insertsmustbeofficial THEN raise_application_error(-20400, 'New Themes can only be inserted by Official Changes');

WHEN themedescriptionmandatory THEN raise_application_error(-20400 , 'If Pharma Rx Portfolio Project is set to "No", then the Theme Description must be filled');

WHEN theme_desc_not_unique THEN raise_application_error(-20400, 'This Theme Description already exists');

WHEN portf_proj_mol_cre_err THEN raise_application_error(-20120, 'MDM_V_THEMES_IOF');

WHEN debugging THEN raise_application_error(-20900, 'Debug in Themes IOF standard');

END;