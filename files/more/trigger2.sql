DECLARE
    ERR_MAP_EXISTS EXCEPTION;
    ERR_MOLEC_ID_MISSING EXCEPTION;
    ERR_NO_PORTF_MOLECULE_LEFT EXCEPTION;
    ERR_UPD_INV_MAP EXCEPTION;
    ERR_INS_INV_MAP EXCEPTION;
    ERR_INV_MOL_SEQUENCE EXCEPTION;
    UPDATE_UPD EXCEPTION;
    V_COUNT_T_MAPPINGS         PLS_INTEGER; -- how many for one theme
    V_COUNT_T_MOL_MAP          PLS_INTEGER; -- how many for one theme/molecule combination (zero/one expected)
    V_MOLECULE_SEQ_NO          PLS_INTEGER;
    V_SEQ_NO_DUPLICATE_CNT     PLS_INTEGER;
    INVALID_MAPPING_EXISTS     BOOLEAN := FALSE;
    V_MANUAL_SHORT_DESC        THEMES.MANUAL_SHORT_DESC%TYPE;
 
    --   v_mappings_changed         BOOLEAN := FALSE;
    --   v_theme_no_upd_molec_map   themes.theme_no%TYPE;
BEGIN
 
    --chevali1
    SELECT
        MANUAL_SHORT_DESC INTO V_MANUAL_SHORT_DESC
    FROM
        GMD.THEMES
    WHERE
        THEME_NO = NVL(:NEW.THEME_NO, :OLD.THEME_NO);
    IF (DELETING) THEN
 /*
        DELETE FROM theme_molecule_map tmm
              WHERE     tmm.theme_no = :old.theme_no
                    AND tmm.molecule_id = :old.molecule_id;
        */
        UPDATE THEME_MOLECULE_MAP TMM
        SET
            TMM.VALID_IND = 'N'
        WHERE
            TMM.THEME_NO = :OLD.THEME_NO
            AND TMM.MOLECULE_ID = :OLD.MOLECULE_ID;
 
        -- move left (valid mappings only)
        UPDATE THEME_MOLECULE_MAP TMM
        SET
            TMM.MOLECULE_SEQ_NO = TMM.MOLECULE_SEQ_NO - 1
        WHERE
            TMM.THEME_NO = :OLD.THEME_NO
            AND TMM.MOLECULE_SEQ_NO > :OLD.MOLECULE_SEQ_NO
            AND TMM.VALID_IND = 'Y';
 
        --   v_mappings_changed := TRUE;
        --  v_theme_no_upd_molec_map := :old.theme_no;
        -- Update Theme Description
        MDMAPPL.MDM_UTIL_THEMES.REFRESH_THEME_DESC (
            P_THEME_NO => :OLD.THEME_NO,
            P_MOLECULE_ID => :OLD.MOLECULE_ID,
            P_DATE => SYSDATE,
            P_MANUAL_SHORT_DESC => V_MANUAL_SHORT_DESC
        );
    END IF;

    IF (INSERTING OR UPDATING) THEN
        SELECT
            COUNT (*) INTO V_COUNT_T_MAPPINGS
        FROM
            V_THEME_MOLECULE_MAP TMM
        WHERE
            TMM.THEME_NO = :NEW.THEME_NO
            AND TMM.VALID_IND = 'Y';
        IF (:NEW.MOLECULE_ID IS NULL) THEN
            RAISE ERR_MOLEC_ID_MISSING;
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

        IF (UPDATING) THEN
            IF (:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS) THEN
                RAISE ERR_UPD_INV_MAP;
            END IF;
        END IF;
 

        -- Check if theme_no <=> molecule_id valid or invalid mapping exists
        --  for changed molecule_ids
        IF (:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')) THEN
            SELECT
                COUNT (*) INTO V_COUNT_T_MOL_MAP
            FROM
                V_THEME_MOLECULE_MAP TMM
            WHERE
                TMM.THEME_NO = :NEW.THEME_NO
                AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID
                AND TMM.VALID_IND = 'Y';
            IF (V_COUNT_T_MOL_MAP > 0) THEN
                RAISE ERR_MAP_EXISTS;
            END IF;

            SELECT
                COUNT (*) INTO V_COUNT_T_MOL_MAP
            FROM
                V_THEME_MOLECULE_MAP TMM
            WHERE
                TMM.THEME_NO = :NEW.THEME_NO
                AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID
                AND TMM.VALID_IND = 'N';
            IF (V_COUNT_T_MOL_MAP > 0) THEN
                INVALID_MAPPING_EXISTS := TRUE;
            END IF;
        END IF;

        IF (INSERTING) THEN
            CASE
                WHEN :NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1 THEN
                    IF (INVALID_MAPPING_EXISTS) THEN
 
                        -- update to valid, place mapping at the end
                        UPDATE THEME_MOLECULE_MAP TMM
                        SET
                            TMM.VALID_IND = 'Y',
                            TMM.MOLECULE_SEQ_NO = :NEW.MOLECULE_SEQ_NO
                        WHERE
                            TMM.THEME_NO = :NEW.THEME_NO
                            AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID;
                    ELSE -- this is a real new mapping => insert
                        -- insert new, valid mapping at the end
                        INSERT INTO THEME_MOLECULE_MAP TMM (
                            TMM.THEME_NO,
                            TMM.MOLECULE_ID,
                            TMM.MOLECULE_SEQ_NO,
                            TMM.MOLECULE_MAP_CHAR,
                            TMM.VALID_IND
                        ) VALUES (
                            :NEW.THEME_NO,
                            :NEW.MOLECULE_ID,
                            :NEW.MOLECULE_SEQ_NO,
                            :NEW.MOLECULE_MAP_CHAR,
                            'Y'
                        );
                    END IF;
 
                --    v_mappings_changed := TRUE;
                --    v_theme_no_upd_molec_map := :new.theme_no;
                WHEN :NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1 THEN -- move existing and insert mapping
                -- move valid mappings right
                    UPDATE THEME_MOLECULE_MAP TMM
                    SET
                        TMM.MOLECULE_SEQ_NO = TMM.MOLECULE_SEQ_NO + 1
                    WHERE
                        TMM.THEME_NO = :NEW.THEME_NO
                        AND TMM.MOLECULE_SEQ_NO >= :NEW.MOLECULE_SEQ_NO
                        AND TMM.VALID_IND = 'Y';
 
                -- place new mapping on new position
                    IF (INVALID_MAPPING_EXISTS) THEN
 
                        -- update to valid, place mapping at new position
                        UPDATE THEME_MOLECULE_MAP TMM
                        SET
                            TMM.VALID_IND = 'Y',
                            TMM.MOLECULE_SEQ_NO = :NEW.MOLECULE_SEQ_NO
                        WHERE
                            TMM.THEME_NO = :NEW.THEME_NO
                            AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID;
                    ELSE -- this is a real new mapping => insert
                        -- insert mapping on new position
                        INSERT INTO THEME_MOLECULE_MAP TMM (
                            TMM.THEME_NO,
                            TMM.MOLECULE_ID,
                            TMM.MOLECULE_SEQ_NO,
                            TMM.MOLECULE_MAP_CHAR,
                            TMM.VALID_IND
                        ) VALUES (
                            :NEW.THEME_NO,
                            :NEW.MOLECULE_ID,
                            :NEW.MOLECULE_SEQ_NO,
                            :NEW.MOLECULE_MAP_CHAR,
                            'Y'
                        );
                    END IF;
 
                --    v_mappings_changed := TRUE;
                --    v_theme_no_upd_molec_map := :new.theme_no;
                ELSE
 
                --(:new.molecule_seq_no < v_count_t_mappings + 1)
                    RAISE ERR_INS_INV_MAP;
            END CASE; ------------- INSERTING-CASES ----------------------------
        END IF; ---INSERTING -------------------------------------------
        IF (UPDATING) THEN
            IF (:NEW.MOLECULE_ID IS NOT NULL) THEN
                IF (:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR) THEN
                    UPDATE THEME_MOLECULE_MAP TMM
                    SET
                        TMM.MOLECULE_MAP_CHAR = :NEW.MOLECULE_MAP_CHAR
                    WHERE
                        TMM.THEME_NO = :NEW.THEME_NO
                        AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID;
                END IF;

                IF (:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO) THEN -- BLOCK START  existing molecule is moved (update seq_no)
                    -- existing molecule is moved (update seq_no)
                    -- delete old mapping

 /*
                    DELETE FROM theme_molecule_map tmm
                          WHERE     tmm.theme_no = :new.theme_no
                                AND tmm.molecule_id = :old.molecule_id;
                    */
                    UPDATE THEME_MOLECULE_MAP TMM
                    SET
                        TMM.VALID_IND = 'N'
                    WHERE
                        TMM.THEME_NO = :NEW.THEME_NO
                        AND TMM.MOLECULE_ID = :OLD.MOLECULE_ID;
                    IF (:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO) THEN
 
                        -- move valid mappings left
                        UPDATE THEME_MOLECULE_MAP TMM
                        SET
                            TMM.MOLECULE_SEQ_NO = TMM.MOLECULE_SEQ_NO - 1
                        WHERE
                            TMM.THEME_NO = :NEW.THEME_NO
                            AND TMM.MOLECULE_SEQ_NO > :OLD.MOLECULE_SEQ_NO
                            AND TMM.VALID_IND = 'Y'
                            AND TMM.MOLECULE_SEQ_NO <= :NEW.MOLECULE_SEQ_NO;
                    ELSE
 
                        -- move valid mappings right
                        UPDATE THEME_MOLECULE_MAP TMM
                        SET
                            TMM.MOLECULE_SEQ_NO = TMM.MOLECULE_SEQ_NO + 1
                        WHERE
                            TMM.THEME_NO = :NEW.THEME_NO
                            AND TMM.VALID_IND = 'Y'
                            AND TMM.MOLECULE_SEQ_NO >= :NEW.MOLECULE_SEQ_NO
                            AND TMM.MOLECULE_SEQ_NO < :OLD.MOLECULE_SEQ_NO;
                    END IF;
 

                    -- place valid mapping on new position
                    IF (INVALID_MAPPING_EXISTS) THEN
 
                        -- update to valid, place mapping at new position
                        UPDATE THEME_MOLECULE_MAP TMM
                        SET
                            TMM.VALID_IND = 'Y',
                            TMM.MOLECULE_SEQ_NO = :NEW.MOLECULE_SEQ_NO,
                            TMM.MOLECULE_MAP_CHAR =: NEW.MOLECULE_MAP_CHAR
                        WHERE
                            TMM.THEME_NO = :NEW.THEME_NO
                            AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID;
                    ELSE -- this is a real new mapping => insert
                        -- insert mapping on new position
                        INSERT INTO THEME_MOLECULE_MAP TMM (
                            TMM.THEME_NO,
                            TMM.MOLECULE_ID,
                            TMM.MOLECULE_SEQ_NO,
                            TMM.MOLECULE_MAP_CHAR,
                            TMM.VALID_IND
                        ) VALUES (
                            :NEW.THEME_NO,
                            :NEW.MOLECULE_ID,
                            :NEW.MOLECULE_SEQ_NO,
                            :NEW.MOLECULE_MAP_CHAR,
                            'Y'
                        );
                    END IF;
 

                    --   v_mappings_changed := TRUE;
                    --   v_theme_no_upd_molec_map := :new.theme_no;
                END IF;
 

                -- BLOCK END  existing molecule is moved (update seq_no)
            END IF;

            IF (:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO) THEN -- BLOCK START  new molecule in arbitrary position
                -- we know that the new mapping doesn't exist yet
                -- we know that the old mapping exists
                -- old mapping  is removed
                -- new mapping is inserted

 /*
                DELETE FROM theme_molecule_map tmm
                      WHERE     tmm.theme_no = :new.theme_no
                            AND tmm.molecule_id = :old.molecule_id;
                            */
                UPDATE THEME_MOLECULE_MAP TMM
                SET
                    TMM.VALID_IND = 'N'
                WHERE
                    TMM.THEME_NO = :NEW.THEME_NO
                    AND TMM.MOLECULE_ID = :OLD.MOLECULE_ID;
 
                -- move valid mappings left
                UPDATE THEME_MOLECULE_MAP TMM
                SET
                    TMM.MOLECULE_SEQ_NO = TMM.MOLECULE_SEQ_NO - 1
                WHERE
                    TMM.THEME_NO = :NEW.THEME_NO
                    AND TMM.MOLECULE_SEQ_NO > :OLD.MOLECULE_SEQ_NO
                    AND TMM.MOLECULE_SEQ_NO <= :NEW.MOLECULE_SEQ_NO
                    AND TMM.VALID_IND = 'Y';
 
                -- place new mapping on new position
                IF (INVALID_MAPPING_EXISTS) THEN
 
                    -- update to valid, update molecule_map_char, place mapping at new position
                    UPDATE THEME_MOLECULE_MAP TMM
                    SET
                        TMM.VALID_IND = 'Y',
                        TMM.MOLECULE_SEQ_NO = :NEW.MOLECULE_SEQ_NO,
                        TMM.MOLECULE_MAP_CHAR =:NEW.MOLECULE_MAP_CHAR
                    WHERE
                        TMM.THEME_NO = :NEW.THEME_NO
                        AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID;
                ELSE -- this is a real new mapping => insert
                    -- insert mapping on new position
                    INSERT INTO THEME_MOLECULE_MAP TMM (
                        TMM.THEME_NO,
                        TMM.MOLECULE_ID,
                        TMM.MOLECULE_SEQ_NO,
                        TMM.MOLECULE_MAP_CHAR,
                        TMM.VALID_IND
                    ) VALUES (
                        :NEW.THEME_NO,
                        :NEW.MOLECULE_ID,
                        :NEW.MOLECULE_SEQ_NO,
                        :NEW.MOLECULE_MAP_CHAR,
                        'Y'
                    );
                END IF;
 

                --  v_mappings_changed := TRUE;
                --  v_theme_no_upd_molec_map := :new.theme_no;
            END IF; -- BLOCK END  new molecule in arbitrary position
            IF (:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO THEN -- BLOCK START  new molecule in existing position
                -- old mapping  is removed
                -- new mapping is inserted
                UPDATE THEME_MOLECULE_MAP TMM
                SET
                    TMM.VALID_IND = 'N'
                WHERE
                    TMM.THEME_NO = :NEW.THEME_NO
                    AND TMM.MOLECULE_ID = :OLD.MOLECULE_ID
                    AND MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO; -- insert mapping on new position
                -- place new mapping on position
                IF (INVALID_MAPPING_EXISTS) THEN
 
                    -- update to valid, place mapping at new position
                    UPDATE THEME_MOLECULE_MAP TMM
                    SET
                        TMM.VALID_IND = 'Y',
                        TMM.MOLECULE_SEQ_NO = :NEW.MOLECULE_SEQ_NO,
                        TMM.MOLECULE_MAP_CHAR =:NEW.MOLECULE_MAP_CHAR
                    WHERE
                        TMM.THEME_NO = :NEW.THEME_NO
                        AND TMM.MOLECULE_ID = :NEW.MOLECULE_ID;
                ELSE -- this is a real new mapping => insert
                    -- insert mapping on position
                    INSERT INTO THEME_MOLECULE_MAP TMM (
                        TMM.THEME_NO,
                        TMM.MOLECULE_ID,
                        TMM.MOLECULE_SEQ_NO,
                        TMM.MOLECULE_MAP_CHAR
                    ) VALUES (
                        :NEW.THEME_NO,
                        :NEW.MOLECULE_ID,
                        :NEW.MOLECULE_SEQ_NO,
                        :NEW.MOLECULE_MAP_CHAR
                    );
                END IF;
 

                --  v_mappings_changed := TRUE;
                --  v_theme_no_upd_molec_map := :new.theme_no;
            END IF; -- BLOCK END  new molecule in existing position
        END IF; -------------------------------------------------- UPDATING
        -- Update Theme Description
        MDMAPPL.MDM_UTIL_THEMES.REFRESH_THEME_DESC (
            P_THEME_NO => :NEW.THEME_NO,
            P_MOLECULE_ID => 0,
            P_DATE => SYSDATE,
            P_MANUAL_SHORT_DESC => V_MANUAL_SHORT_DESC
        );
    END IF; ---------------------------------------- INSERTING or UPDATING
    -- Sanity check => each seq_no may appear only once for valid Mappings
    SELECT
        COUNT (*) INTO V_SEQ_NO_DUPLICATE_CNT
    FROM
        (
            SELECT
                MOLECULE_SEQ_NO
            FROM
                THEME_MOLECULE_MAP TMM
            WHERE
                TMM.THEME_NO = :NEW.THEME_NO
                AND VALID_IND = 'Y'
            GROUP BY
                MOLECULE_SEQ_NO
            HAVING
                COUNT (*) > 1
        );
    IF (V_SEQ_NO_DUPLICATE_CNT > 0) THEN
        RAISE ERR_INV_MOL_SEQUENCE;
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
    WHEN ERR_MAP_EXISTS THEN
        RAISE_APPLICATION_ERROR (-20110, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN ERR_MOLEC_ID_MISSING THEN
        RAISE_APPLICATION_ERROR (-20111, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN ERR_UPD_INV_MAP THEN
        RAISE_APPLICATION_ERROR (-20112, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN ERR_INS_INV_MAP THEN
        RAISE_APPLICATION_ERROR (-20113, 'MDM_THEME_MOLECULE_MAP_IOF');
    WHEN ERR_INV_MOL_SEQUENCE THEN
        RAISE_APPLICATION_ERROR (-20120, 'MDM_THEME_MOLECULE_MAP_IOF');
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