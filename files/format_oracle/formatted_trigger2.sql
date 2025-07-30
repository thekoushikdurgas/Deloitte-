DECLARE err_map_exists
EXCEPTION;

err_molec_id_missing
EXCEPTION;

err_no_portf_molecule_left
EXCEPTION;

err_upd_inv_map
EXCEPTION;

err_ins_inv_map
EXCEPTION;

err_inv_mol_sequence
EXCEPTION;

update_upd
EXCEPTION;

v_count_t_mappings PLS_INTEGER;

v_count_t_mol_map PLS_INTEGER;

v_molecule_seq_no PLS_INTEGER;

v_seq_no_duplicate_cnt PLS_INTEGER;

invalid_mapping_exists BOOLEAN := FALSE;

v_manual_short_desc themes.manual_short_desc%TYPE;

BEGIN
SELECT manual_short_desc INTO v_manual_short_desc
FROM gmd.themes
WHERE theme_no = nvl(:new.theme_no, :old.theme_no);

IF (deleting) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'N'
WHERE tmm.theme_no = :old.theme_no
    AND tmm.molecule_id = :old.molecule_id;


UPDATE theme_molecule_map tmm
SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
WHERE tmm.theme_no = :old.theme_no
    AND tmm.molecule_seq_no > :old.molecule_seq_no
    AND tmm.valid_ind = 'Y';

mdmappl.mdm_util_themes.refresh_theme_desc (p_theme_no => :old.theme_no , p_molecule_id => :old.molecule_id , p_date => sysdate , p_manual_short_desc => v_manual_short_desc);

END IF;

IF (inserting
    OR updating) THEN
SELECT COUNT (*) INTO v_count_t_mappings
FROM v_theme_molecule_map tmm
WHERE tmm.theme_no = :new.theme_no
    AND tmm.valid_ind = 'Y';

IF (:new.molecule_id IS NULL) THEN RAISE err_molec_id_missing;

END IF;

IF (updating) THEN IF (:new.molecule_seq_no > v_count_t_mappings) THEN RAISE err_upd_inv_map;

END IF;

END IF;

IF (:new.molecule_id <> NVL (:old.molecule_id,
                                  '-1')) THEN
SELECT COUNT (*) INTO v_count_t_mol_map
FROM v_theme_molecule_map tmm
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id
    AND tmm.valid_ind = 'Y';

IF (v_count_t_mol_map > 0) THEN RAISE err_map_exists;

END IF;


SELECT COUNT (*) INTO v_count_t_mol_map
FROM v_theme_molecule_map tmm
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id
    AND tmm.valid_ind = 'N';

IF (v_count_t_mol_map > 0) THEN invalid_mapping_exists := TRUE;

END IF;

END IF;

IF (inserting) THEN CASE WHEN :new.molecule_seq_no = v_count_t_mappings + 1 THEN IF (invalid_mapping_exists) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'Y' ,
    tmm.molecule_seq_no = :new.molecule_seq_no
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id;

ELSE
INSERT INTO theme_molecule_map tmm (tmm.theme_no , tmm.molecule_id , tmm.molecule_seq_no , tmm.molecule_map_char , tmm.valid_ind)
VALUES (:new.theme_no , :new.molecule_id , :new.molecule_seq_no , :new.molecule_map_char , 'Y');

END IF;

WHEN :new.molecule_seq_no < v_count_t_mappings + 1 THEN
UPDATE theme_molecule_map tmm
SET tmm.molecule_seq_no = tmm.molecule_seq_no + 1
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_seq_no >= :new.molecule_seq_no
    AND tmm.valid_ind = 'Y';

IF (invalid_mapping_exists) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'Y' ,
    tmm.molecule_seq_no = :new.molecule_seq_no
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id;

ELSE
INSERT INTO theme_molecule_map tmm (tmm.theme_no , tmm.molecule_id , tmm.molecule_seq_no , tmm.molecule_map_char , tmm.valid_ind)
VALUES (:new.theme_no , :new.molecule_id , :new.molecule_seq_no , :new.molecule_map_char , 'Y');

END IF;

ELSE RAISE err_ins_inv_map;

END CASE;

END IF;

IF (updating) THEN IF (:new.molecule_id IS NOT NULL) THEN IF (:new.molecule_id = :old.molecule_id
                                                              AND :new.molecule_seq_no = :old.molecule_seq_no)
AND :new.molecule_map_char <> :old.molecule_map_char THEN
UPDATE theme_molecule_map tmm
SET tmm.molecule_map_char = :new.molecule_map_char
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id;

END IF;

IF (:new.molecule_id = :old.molecule_id
    AND :new.molecule_seq_no <> :old.molecule_seq_no) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'N'
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :old.molecule_id;

IF (:old.molecule_seq_no < :new.molecule_seq_no) THEN
UPDATE theme_molecule_map tmm
SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_seq_no > :old.molecule_seq_no
    AND tmm.valid_ind = 'Y'
    AND tmm.molecule_seq_no <= :new.molecule_seq_no;

ELSE
UPDATE theme_molecule_map tmm
SET tmm.molecule_seq_no = tmm.molecule_seq_no + 1
WHERE tmm.theme_no = :new.theme_no
    AND tmm.valid_ind = 'Y'
    AND tmm.molecule_seq_no >= :new.molecule_seq_no
    AND tmm.molecule_seq_no < :old.molecule_seq_no;

END IF;

IF (invalid_mapping_exists) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'Y' ,
    tmm.molecule_seq_no = :new.molecule_seq_no ,
                               tmm.molecule_map_char =: new.molecule_map_char
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id;

ELSE
INSERT INTO theme_molecule_map tmm (tmm.theme_no , tmm.molecule_id , tmm.molecule_seq_no , tmm.molecule_map_char , tmm.valid_ind)
VALUES (:new.theme_no , :new.molecule_id , :new.molecule_seq_no , :new.molecule_map_char , 'Y');

END IF;

END IF;

END IF;

IF (:new.molecule_id <> :old.molecule_id
    AND :new.molecule_seq_no <> :old.molecule_seq_no) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'N'
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :old.molecule_id;


UPDATE theme_molecule_map tmm
SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_seq_no > :old.molecule_seq_no
    AND tmm.molecule_seq_no <= :new.molecule_seq_no
    AND tmm.valid_ind = 'Y';

IF (invalid_mapping_exists) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'Y' ,
    tmm.molecule_seq_no = :new.molecule_seq_no ,
                               tmm.molecule_map_char =:new.molecule_map_char
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id;

ELSE
INSERT INTO theme_molecule_map tmm (tmm.theme_no , tmm.molecule_id , tmm.molecule_seq_no , tmm.molecule_map_char , tmm.valid_ind)
VALUES (:new.theme_no , :new.molecule_id , :new.molecule_seq_no , :new.molecule_map_char , 'Y');

END IF;

END IF;

IF (:new.molecule_id <> :old.molecule_id)
AND :new.molecule_seq_no = :old.molecule_seq_no THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'N'
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :old.molecule_id
    AND molecule_seq_no = :old.molecule_seq_no;

IF (invalid_mapping_exists) THEN
UPDATE theme_molecule_map tmm
SET tmm.valid_ind = 'Y' ,
    tmm.molecule_seq_no = :new.molecule_seq_no ,
                               tmm.molecule_map_char =:new.molecule_map_char
WHERE tmm.theme_no = :new.theme_no
    AND tmm.molecule_id = :new.molecule_id;

ELSE
INSERT INTO theme_molecule_map tmm (tmm.theme_no , tmm.molecule_id , tmm.molecule_seq_no , tmm.molecule_map_char)
VALUES (:new.theme_no , :new.molecule_id , :new.molecule_seq_no , :new.molecule_map_char);

END IF;

END IF;

END IF;

mdmappl.mdm_util_themes.refresh_theme_desc (p_theme_no => :new.theme_no , p_molecule_id => 0 , p_date => sysdate , p_manual_short_desc => v_manual_short_desc);

END IF;


SELECT COUNT (*) INTO v_seq_no_duplicate_cnt
FROM
    (SELECT molecule_seq_no
     FROM theme_molecule_map tmm
     WHERE tmm.theme_no = :new.theme_no
         AND valid_ind = 'Y'
     GROUP BY molecule_seq_no
     HAVING COUNT (*) > 1);

IF (v_seq_no_duplicate_cnt > 0) THEN RAISE err_inv_mol_sequence;

END IF;


EXCEPTION WHEN err_map_exists THEN raise_application_error (-20110, 'MDM_THEME_MOLECULE_MAP_IOF');

WHEN err_molec_id_missing THEN raise_application_error (-20111, 'MDM_THEME_MOLECULE_MAP_IOF');

WHEN err_upd_inv_map THEN raise_application_error (-20112, 'MDM_THEME_MOLECULE_MAP_IOF');

WHEN err_ins_inv_map THEN raise_application_error (-20113, 'MDM_THEME_MOLECULE_MAP_IOF');

WHEN err_inv_mol_sequence THEN raise_application_error (-20120, 'MDM_THEME_MOLECULE_MAP_IOF');

END;