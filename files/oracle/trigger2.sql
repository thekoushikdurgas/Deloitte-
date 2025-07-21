declare
    err_map_exists               EXCEPTION;
    err_molec_id_missing         EXCEPTION;
    err_no_portf_molecule_left   EXCEPTION;
    err_upd_inv_map              EXCEPTION;
    err_ins_inv_map              EXCEPTION;
    err_inv_mol_sequence         EXCEPTION;
    update_upd                   EXCEPTION;
    v_count_t_mappings           PLS_INTEGER;        -- how many for one theme
    v_count_t_mol_map            PLS_INTEGER; -- how many for one theme/molecule combination (zero/one expected)
    v_molecule_seq_no            PLS_INTEGER;
    v_seq_no_duplicate_cnt       PLS_INTEGER;
    invalid_mapping_exists       BOOLEAN := FALSE;
    v_manual_short_desc          THEMES.MANUAL_SHORT_DESC%TYPE;
--   v_mappings_changed         BOOLEAN := FALSE;
--   v_theme_no_upd_molec_map   themes.theme_no%TYPE;


BEGIN
     --chevali1
        SELECT manual_short_desc
        INTO v_manual_short_desc
        from gmd.themes
        where theme_no = NVL(:new.theme_no, :old.theme_no);


    IF (DELETING)
    THEN
        /*
        DELETE FROM theme_molecule_map tmm
              WHERE     tmm.theme_no = :old.theme_no
                    AND tmm.molecule_id = :old.molecule_id;
        */
        UPDATE theme_molecule_map tmm
           SET tmm.valid_ind = 'N'
         WHERE     tmm.theme_no = :old.theme_no
               AND tmm.molecule_id = :old.molecule_id;


        -- move left (valid mappings only)


        UPDATE theme_molecule_map tmm
           SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
         WHERE     tmm.theme_no = :old.theme_no
               AND tmm.molecule_seq_no > :old.molecule_seq_no
               AND tmm.valid_ind = 'Y';


        --   v_mappings_changed := TRUE;
        --  v_theme_no_upd_molec_map := :old.theme_no;






        -- Update Theme Description
        mdmappl.mdm_util_themes.refresh_theme_desc (
            p_theme_no      => :old.theme_no
           ,p_molecule_id   => :old.molecule_id
           ,p_date          => SYSDATE
           ,p_manual_short_desc => v_manual_short_desc);




    END IF;






    IF (INSERTING OR UPDATING)
    THEN                 -- select number of valid mappings for given theme_no
        SELECT COUNT (*)
          INTO v_count_t_mappings
          FROM v_theme_molecule_map tmm
         WHERE tmm.theme_no = :new.theme_no AND tmm.valid_ind = 'Y';


        IF (:new.molecule_id IS NULL)
        THEN
            RAISE err_molec_id_missing;
        /*
        -- DELETE does not work because refresh doesn't find the record
        -----------------------------------------------------------------
        -- delete the mapping to this molecule
        DELETE FROM theme_molecule_map tmm
              WHERE     tmm.theme_no = :old.theme_no
                    AND tmm.molecule_id = :old.molecule_id;


        -- move left


        UPDATE theme_molecule_map tmm
           SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
         WHERE     tmm.theme_no = :old.theme_no
               AND tmm.molecule_seq_no > :old.molecule_seq_no;
         */
        END IF;


        IF (UPDATING)
        THEN
            IF (:new.molecule_seq_no > v_count_t_mappings)
            THEN
                RAISE err_upd_inv_map;
            END IF;
        END IF;




        -- Check if theme_no <=> molecule_id valid or invalid mapping exists
        --  for changed molecule_ids




        IF (:new.molecule_id <> NVL (:old.molecule_id, '-1'))
        THEN
            SELECT COUNT (*)
              INTO v_count_t_mol_map
              FROM v_theme_molecule_map tmm
             WHERE     tmm.theme_no = :new.theme_no
                   AND tmm.molecule_id = :new.molecule_id
                   AND tmm.valid_ind = 'Y';




            IF (v_count_t_mol_map > 0)
            THEN
                RAISE err_map_exists;
            END IF;


            SELECT COUNT (*)
              INTO v_count_t_mol_map
              FROM v_theme_molecule_map tmm
             WHERE     tmm.theme_no = :new.theme_no
                   AND tmm.molecule_id = :new.molecule_id
                   AND tmm.valid_ind = 'N';


            IF (v_count_t_mol_map > 0)
            THEN
                invalid_mapping_exists := TRUE;
            END IF;
        END IF;






        IF (INSERTING)
        THEN
            CASE
                WHEN :new.molecule_seq_no = v_count_t_mappings + 1
                THEN
                    IF (invalid_mapping_exists)
                    THEN
                        -- update to valid, place mapping at the end
                        UPDATE theme_molecule_map tmm
                           SET tmm.valid_ind = 'Y'
                              ,tmm.molecule_seq_no = :new.molecule_seq_no
                         WHERE     tmm.theme_no = :new.theme_no
                               AND tmm.molecule_id = :new.molecule_id;
                    ELSE               -- this is a real new mapping => insert
                        -- insert new, valid mapping at the end
                        INSERT
                          INTO theme_molecule_map tmm (tmm.theme_no
                                                      ,tmm.molecule_id
                                                      ,tmm.molecule_seq_no
                                                      ,tmm.molecule_map_char
                                                      ,tmm.valid_ind)
                        VALUES (
                               :new.theme_no
                               ,:new.molecule_id
                               ,:new.molecule_seq_no
                               ,:new.molecule_map_char
                               ,'Y');
                    END IF;
                --    v_mappings_changed := TRUE;
                --    v_theme_no_upd_molec_map := :new.theme_no;


                WHEN :new.molecule_seq_no < v_count_t_mappings + 1
                THEN                       -- move existing and insert mapping
                    -- move valid mappings right


                    UPDATE theme_molecule_map tmm
                       SET tmm.molecule_seq_no = tmm.molecule_seq_no + 1
                     WHERE     tmm.theme_no = :new.theme_no
                           AND tmm.molecule_seq_no >= :new.molecule_seq_no
                           AND tmm.valid_ind = 'Y';


                    -- place new mapping on new position
                    IF (invalid_mapping_exists)
                    THEN
                        -- update to valid, place mapping at new position
                        UPDATE theme_molecule_map tmm
                           SET tmm.valid_ind = 'Y'
                              ,tmm.molecule_seq_no = :new.molecule_seq_no
                         WHERE     tmm.theme_no = :new.theme_no
                               AND tmm.molecule_id = :new.molecule_id;
                    ELSE               -- this is a real new mapping => insert
                        -- insert mapping on new position


                        INSERT
                          INTO theme_molecule_map tmm (tmm.theme_no
                                                      ,tmm.molecule_id
                                                      ,tmm.molecule_seq_no
                                                      ,tmm.molecule_map_char
                                                      ,tmm.valid_ind)
                        VALUES (:new.theme_no
                               ,:new.molecule_id
                               ,:new.molecule_seq_no
                               ,:new.molecule_map_char
                               ,'Y');
                    END IF;
                --    v_mappings_changed := TRUE;
                --    v_theme_no_upd_molec_map := :new.theme_no;
                ELSE
                    --(:new.molecule_seq_no < v_count_t_mappings + 1)
                    RAISE err_ins_inv_map;
            END CASE; ------------- INSERTING-CASES ----------------------------
        END IF;       ---INSERTING -------------------------------------------


        IF (UPDATING)
        THEN
            IF (:new.molecule_id IS NOT NULL)
            THEN
                IF (:new.molecule_id = :old.molecule_id AND :new.molecule_seq_no = :old.molecule_seq_no)
                AND :new.molecule_map_char <> :old.molecule_map_char
                then
                UPDATE theme_molecule_map tmm
                       SET tmm.molecule_map_char = :new.molecule_map_char
                     WHERE     tmm.theme_no = :new.theme_no
                           AND tmm.molecule_id = :new.molecule_id;
                end if;


                IF (:new.molecule_id = :old.molecule_id AND :new.molecule_seq_no <> :old.molecule_seq_no)
                THEN -- BLOCK START  existing molecule is moved (update seq_no)
                    -- existing molecule is moved (update seq_no)
                    -- delete old mapping
                    /*
                    DELETE FROM theme_molecule_map tmm
                          WHERE     tmm.theme_no = :new.theme_no
                                AND tmm.molecule_id = :old.molecule_id;
                    */
                    UPDATE theme_molecule_map tmm
                       SET tmm.valid_ind = 'N'
                     WHERE     tmm.theme_no = :new.theme_no
                           AND tmm.molecule_id = :old.molecule_id;


                    IF (:old.molecule_seq_no < :new.molecule_seq_no)
                    THEN
                        -- move valid mappings left
                        UPDATE theme_molecule_map tmm
                           SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
                         WHERE     tmm.theme_no = :new.theme_no
                               AND tmm.molecule_seq_no > :old.molecule_seq_no
                               AND tmm.valid_ind = 'Y'
                               AND tmm.molecule_seq_no <=
                                       :new.molecule_seq_no;
                    ELSE
                        -- move valid mappings right
                        UPDATE theme_molecule_map tmm
                           SET tmm.molecule_seq_no = tmm.molecule_seq_no + 1
                         WHERE     tmm.theme_no = :new.theme_no
                               AND tmm.valid_ind = 'Y'
                               AND tmm.molecule_seq_no >=
                                       :new.molecule_seq_no
                               AND tmm.molecule_seq_no < :old.molecule_seq_no;
                    END IF;


                    -- place valid mapping on new position
                    IF (invalid_mapping_exists)
                    THEN
                        -- update to valid, place mapping at new position
                        UPDATE theme_molecule_map tmm
                           SET tmm.valid_ind = 'Y'
                              ,tmm.molecule_seq_no = :new.molecule_seq_no
                              ,tmm.molecule_map_char =: new.molecule_map_char
                         WHERE     tmm.theme_no = :new.theme_no
                               AND tmm.molecule_id = :new.molecule_id;
                    ELSE               -- this is a real new mapping => insert
                        -- insert mapping on new position


                        INSERT
                          INTO theme_molecule_map tmm (tmm.theme_no
                                                      ,tmm.molecule_id
                                                      ,tmm.molecule_seq_no
                                                      ,tmm.molecule_map_char
                                                      ,tmm.valid_ind)
                        VALUES (:new.theme_no
                               ,:new.molecule_id
                               ,:new.molecule_seq_no
                               ,:new.molecule_map_char
                               ,'Y');
                    END IF;
                --   v_mappings_changed := TRUE;
                --   v_theme_no_upd_molec_map := :new.theme_no;
                END IF;
            -- BLOCK END  existing molecule is moved (update seq_no)
            END IF;


            IF (:new.molecule_id <> :old.molecule_id AND :new.molecule_seq_no <> :old.molecule_seq_no)
            THEN            -- BLOCK START  new molecule in arbitrary position
                -- we know that the new mapping doesn't exist yet
                -- we know that the old mapping exists
                -- old mapping  is removed
                -- new mapping is inserted
                /*
                DELETE FROM theme_molecule_map tmm
                      WHERE     tmm.theme_no = :new.theme_no
                            AND tmm.molecule_id = :old.molecule_id;
                            */
                UPDATE theme_molecule_map tmm
                   SET tmm.valid_ind = 'N'
                 WHERE     tmm.theme_no = :new.theme_no
                       AND tmm.molecule_id = :old.molecule_id;


                -- move valid mappings left


                UPDATE theme_molecule_map tmm
                   SET tmm.molecule_seq_no = tmm.molecule_seq_no - 1
                 WHERE     tmm.theme_no = :new.theme_no
                       AND tmm.molecule_seq_no > :old.molecule_seq_no
                       AND tmm.molecule_seq_no <= :new.molecule_seq_no
                       AND tmm.valid_ind = 'Y';


                -- place new mapping on new position
                IF (invalid_mapping_exists)
                THEN
                    -- update to valid, update molecule_map_char, place mapping at new position
                    UPDATE theme_molecule_map tmm
                       SET tmm.valid_ind = 'Y'
                          ,tmm.molecule_seq_no = :new.molecule_seq_no
                          ,tmm.molecule_map_char =:new.molecule_map_char
                     WHERE     tmm.theme_no = :new.theme_no
                           AND tmm.molecule_id = :new.molecule_id;
                ELSE                   -- this is a real new mapping => insert
                    -- insert mapping on new position
                    INSERT INTO theme_molecule_map tmm (tmm.theme_no
                                                       ,tmm.molecule_id
                                                       ,tmm.molecule_seq_no
                                                       ,tmm.molecule_map_char
                                                       ,tmm.valid_ind)
                    VALUES (:new.theme_no
                           ,:new.molecule_id
                           ,:new.molecule_seq_no
                           ,:new.molecule_map_char
                           ,'Y');
                END IF;
            --  v_mappings_changed := TRUE;
            --  v_theme_no_upd_molec_map := :new.theme_no;
            END IF;           -- BLOCK END  new molecule in arbitrary position


            IF (:new.molecule_id <> :old.molecule_id)
               AND :new.molecule_seq_no = :old.molecule_seq_no
            THEN             -- BLOCK START  new molecule in existing position
                -- old mapping  is removed
                -- new mapping is inserted
                UPDATE theme_molecule_map tmm
                   SET tmm.valid_ind = 'N'
                 WHERE     tmm.theme_no = :new.theme_no
                       AND tmm.molecule_id = :old.molecule_id
                       AND molecule_seq_no = :old.molecule_seq_no; -- insert mapping on new position


                -- place new mapping on position
                IF (invalid_mapping_exists)
                THEN
                    -- update to valid, place mapping at new position
                    UPDATE theme_molecule_map tmm
                       SET tmm.valid_ind = 'Y'
                          ,tmm.molecule_seq_no = :new.molecule_seq_no
                          ,tmm.molecule_map_char =:new.molecule_map_char
                     WHERE     tmm.theme_no = :new.theme_no
                           AND tmm.molecule_id = :new.molecule_id;
                ELSE                   -- this is a real new mapping => insert
                    -- insert mapping on position


                    INSERT
                      INTO theme_molecule_map tmm (tmm.theme_no
                                                  ,tmm.molecule_id
                                                  ,tmm.molecule_seq_no
                                                  ,tmm.molecule_map_char)
                        VALUES (
                                   :new.theme_no
                                  ,:new.molecule_id
                                  ,:new.molecule_seq_no
                                  ,:new.molecule_map_char);
                END IF;
            --  v_mappings_changed := TRUE;
            --  v_theme_no_upd_molec_map := :new.theme_no;
            END IF;            -- BLOCK END  new molecule in existing position
        END IF;    -------------------------------------------------- UPDATING




        -- Update Theme Description
        mdmappl.mdm_util_themes.refresh_theme_desc (
            p_theme_no      => :new.theme_no
           ,p_molecule_id   => 0
           ,p_date          => SYSDATE
           ,p_manual_short_desc => v_manual_short_desc);




    END IF;     ---------------------------------------- INSERTING or UPDATING


    -- Sanity check => each seq_no may appear only once for valid Mappings
    SELECT COUNT (*)
      INTO v_seq_no_duplicate_cnt
      FROM (SELECT molecule_seq_no
              FROM theme_molecule_map tmm
             WHERE tmm.theme_no = :new.theme_no AND valid_ind = 'Y'
            GROUP BY molecule_seq_no
            HAVING COUNT (*) > 1);


    IF (v_seq_no_duplicate_cnt > 0)
    THEN
        RAISE err_inv_mol_sequence;
    END IF;
/*
    IF (v_mappings_changed)
    THEN                  -- store the theme_no for theme with changed mapping
        -- as a description update may be necessary (for portfolio projects)
        gmd.gmd_util_themes.g_theme_no_upd_molec_map :=
            v_theme_no_upd_molec_map;


        -- debugging, remove for production
        INSERT INTO jap_debug_tmmap
                 VALUES (
                            SYSDATE,
                               'MDMAPPL.MDM_THEME_MOLECULE_MAP_IOF => gmd_util_themes.g_theme_no_upd_molec_map: '
                            || gmd_util_themes.g_theme_no_upd_molec_map,
                            NULL);
    END IF;
    */


EXCEPTION
    WHEN err_map_exists
    THEN
        raise_application_error (-20110, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN err_molec_id_missing
    THEN
        raise_application_error (-20111, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN err_upd_inv_map
    THEN
        raise_application_error (-20112, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN err_ins_inv_map
    THEN
        raise_application_error (-20113, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN err_inv_mol_sequence
    THEN
        raise_application_error (-20120, 'MDM_THEME_MOLECULE_MAP_IOF');
/*
WHEN OTHERS
THEN
    raise_application_error (
        -20199,
           v_count_t_mappings
        || ' nm: '
        || :new.molecule_id
        || ' om: '
        || :old.molecule_id
        || ' ms: '
        || :new.molecule_seq_no
        || 'error: '
        || SQLERRM);
        */
END;