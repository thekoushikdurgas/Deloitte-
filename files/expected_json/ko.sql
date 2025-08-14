DO $$

DECLARE
    V_COUNTER                 INTEGER;
    V_CODE                    VARCHAR(2);
    V_ODG_NO                  VARCHAR(2);
    V_RESGRP_CD               VARCHAR(2);
    V_RESLIN_CD               VARCHAR(2);
    V_STATUS_CD               VARCHAR(1);
    V_DBA_CD                  INTEGER;
    V_PORTF_PROJ_CD           VARCHAR(1);
    V_DESCRIPTION             VARCHAR(500);
    V_RESLIN_DESC             VARCHAR(60);
    V_THEME_DESC_LENGTH       INTEGER;
    V_D_REGISTRAT_DATE        DATE;
    V_D_INS_DATE              DATE;
    V_FUTURE_REGISTRAT        DATE;
    V_VALID_TO                DATE;
    V_USERID                  VARCHAR(30);
    V_SEC_MOL_CNT             INTEGER := 0;
    V_MOLECULE_ID             VARCHAR(5) := NULL;
    V_MOLECULE_RG_NO          VARCHAR(20) := NULL;
    V_MOLEC_IN_LIC_PRTNR      VARCHAR(15) := NULL;
    I1                        RECORD;
    V_NEW_RG_NO               GMD.V_THEME_MOLECULES.RG_NO%TYPE;
    V_COMPARATOR_IND          GMD.V_THEME_MOLECULES.COMPARATOR_IND%TYPE;
    V_THEME_DESC_PROPOSAL     MDMAPPL.MDM_V_THEMES_MTN.THEME_DESC_PROPOSAL%TYPE;
    V_SHORT_NAME              VARCHAR(30);
    C_MOLECULE_TYPE_ID        CONSTANT GMD.V_MOLECULE_TYPES.MOLECULE_TYPE_ID%TYPE := 99;
    C_PHARMACOLOGICAL_TYPE_ID CONSTANT GMD.V_PHARMACOLOGICAL_TYPES.PHARMACOLOGICAL_TYPE_ID%TYPE := 19;
    V_EVOLVED_NMP_CNT         INTEGER;
    V_TRADEMARK_NO            GMD.V_THEMES.TRADEMARK_NO%TYPE;
    V_MOLECULE_TYPE_ID        GMD.V_MOLECULE_TYPES.MOLECULE_TYPE_ID%TYPE;
    V_PHARMACOLOGICAL_TYPE_ID GMD.V_PHARMACOLOGICAL_TYPES.PHARMACOLOGICAL_TYPE_ID%TYPE;
BEGIN
    V_USERID:= :INS_USER;
    SELECT
        NEW_RG_NO INTO V_NEW_RG_NO
    FROM
        (
            SELECT
                RN AS NEW_RG_NO
            FROM
                GENERATE_SERIES(6000,
                6999) AS RN EXCEPT
                SELECT
                    RG_NO::INTEGER
                FROM
                    GMD.V_THEME_MOLECULES_MRHUB
        ) AS FREE_RG LIMIT 1;
    IF (:NEW_IN_PREP_IND = 'Y') THEN
        IF (:NEW_PORTF_PROJ_CD <> 'Y') THEN
            RAISE
        EXCEPTION
            'MDM_V_THEMES_IOF: In-prep theme must be portfolio project';
        END IF;

        IF (:NEW_MOLECULE_ID IS NULL) THEN
            CALL TVDXORA_V3_00.TXO_UTIL$SET_WARNING(FORMAT('No Molecule assigned to In-Prep Theme %s!', :NEW_THEME_NO));
            RAISE
        EXCEPTION
            'MDM_V_THEMES_IOF: Molecule Id must be entered';
        END IF;
    END IF;

    IF (:NEW_MOLECULE_ID IS NOT NULL) THEN
        BEGIN
            SELECT
                RG_NO,
                M.COMPARATOR_IND INTO V_MOLECULE_RG_NO,
                V_COMPARATOR_IND
            FROM
                GMD.V_THEME_MOLECULES_MRHUB M
            WHERE
                MOLECULE_ID = CAST(NULLIF(CAST(:NEW_MOLECULE_ID AS TEXT), '') AS NUMERIC)
                AND M.VALID_IND = 'Y';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE EXCEPTION 'MDM_V_THEMES_IOF: This is not a valid Molecule ID';
        END;

        IF (V_MOLECULE_RG_NO IS NULL) THEN
            IF (V_COMPARATOR_IND = 'Y') THEN
                NULL;
            ELSE
                UPDATE GMD.THEME_MOLECULES
                SET
                    RG_NO = V_NEW_RG_NO,
                    UPD_USER= :UPD_USER,
                    UPD_DATE= :UPD_DATE
                WHERE
                    MOLECULE_ID = CAST(NULLIF(CAST(:NEW_MOLECULE_ID AS TEXT), '') AS NUMERIC);
            END IF;
        END IF;
    END IF;

    V_ODG_NO := SUBSTRING(:NEW_RESLIN_DESC_CONCAT FROM 1 FOR 2);
    V_RESGRP_CD := SUBSTRING(:NEW_RESLIN_DESC_CONCAT FROM 4 FOR 2 );
    V_RESLIN_CD := SUBSTRING(:NEW_RESLIN_DESC_CONCAT FROM 7 FOR 2);
    V_RESLIN_DESC := SUBSTRING(:NEW_RESLIN_DESC_CONCAT FROM 12);
    IF (:NEW_STATUS_DESC IS NOT NULL) THEN
        SELECT
            STATUS_CD INTO V_STATUS_CD
        FROM
            MDMAPPL.MDM_V_THEME_STATUS
        WHERE
            STATE_DESC = :NEW_STATUS_DESC;
    ELSE
        V_STATUS_CD := NULL;
    END IF;

    IF (:NEW_DBA_DESC_CONCAT IS NOT NULL) THEN
        SELECT
            DBA_CD INTO V_DBA_CD
        FROM
            MDMAPPL.MDM_V_DISEASE_BIOLOGY_AREAS
        WHERE
            DBA_SHORT_DESC
            || ' - '
            || DBA_DESC = :NEW_DBA_DESC_CONCAT;
    ELSE
        V_DBA_CD := NULL;
    END IF;

    V_MOLEC_IN_LIC_PRTNR := GMD.GMD_UTIL_THEMES$GET_MOLEC_IN_LIC_PRTNR(CAST(:NEW_MOLECULE_ID AS TEXT));
    IF (:NEW_OFFICIAL_IND = 'N') THEN
        V_TRADEMARK_NO := :NEW_TRADEMARK_NO;
    ELSE
        V_TRADEMARK_NO := NULL;
    END IF;

    V_THEME_DESC_PROPOSAL := GMD.GMD_UTIL_THEMES$GET_THEME_SHORT_NAME_MRHUB( CAST(:NEW_THEME_NO AS TEXT), CAST(:NEW_MOLECULE_ID AS TEXT), :NEW_PROD_SHORT_CD, V_ODG_NO, V_RESGRP_CD, V_RESLIN_CD, :NEW_LINE_EXT_INFO, NULL, V_TRADEMARK_NO::TEXT, 'N' );
    IF (:NEW_MANUAL_SHORT_DESC IS NULL
    AND LENGTH(V_THEME_DESC_PROPOSAL) > 30) THEN
        RAISE
    EXCEPTION
        'MDM_V_THEMES_IOF: The automatically generated Short Description Proposal % is too long', V_THEME_DESC_PROPOSAL;
    END IF;

    V_SHORT_NAME := COALESCE(:NEW_MANUAL_SHORT_DESC, V_THEME_DESC_PROPOSAL);
    V_MOLECULE_ID := :NEW_MOLECULE_ID;
    IF (:NEW_PORTF_PROJ_CD = 'Y'
    AND :NEW_MOLECULE_ID IS NULL) THEN
        IF COALESCE(:NEW_MANUAL_SHORT_DESC, :NEW_THEME_DESC_PROPOSAL) IS NULL THEN
            RAISE
        EXCEPTION
            'MDM_V_THEMES_IOF: Portfolio project molecule creation error';
            ELSE
                INSERT INTO GMD.THEME_MOLECULES(
                    MOLECULE_DESC,
                    VALID_IND,
                    RG_NO,
                    CANCER_IMMUNOTHERAPY_IND,
                    MOLECULE_TYPE_ID,
                    PHARMACOLOGICAL_TYPE_ID,
                    INS_USER,
                    INS_DATE
                ) VALUES (
                    COALESCE(:NEW_MANUAL_SHORT_DESC, :NEW_THEME_DESC_PROPOSAL),
                    'Y',
                    V_NEW_RG_NO,
                    'N',
                    C_MOLECULE_TYPE_ID,
                    C_PHARMACOLOGICAL_TYPE_ID,
                    :INS_USER,
                    :INS_DATE
                );
                SELECT
                    MOLECULE_ID INTO V_MOLECULE_ID
                FROM
                    GMD.V_THEME_MOLECULES_MRHUB
                WHERE
                    MOLECULE_DESC = COALESCE(:NEW_MANUAL_SHORT_DESC, :NEW_THEME_DESC_PROPOSAL)
                    AND VALID_IND = 'Y'
                    AND RG_NO = V_NEW_RG_NO
                    AND CANCER_IMMUNOTHERAPY_IND = 'N'
                    AND MOLECULE_TYPE_ID = C_MOLECULE_TYPE_ID
                    AND PHARMACOLOGICAL_TYPE_ID = C_PHARMACOLOGICAL_TYPE_ID;
                INSERT INTO GMD.THEME_MOLECULE_MAP (
                    THEME_NO,
                    MOLECULE_ID,
                    MOLECULE_SEQ_NO,
                    VALID_IND,
                    INS_USER,
                    INS_DATE
                ) VALUES (
                    :NEW_THEME_NO,
                    COALESCE(V_MOLECULE_ID, ''),
                    1,
                    'Y',
                    :INS_USER,
                    :INS_DATE
                );
        END IF;
    END IF;

    IF (LENGTH(CAST(:NEW_THEME_NO AS TEXT)) = 4
    AND (SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 1, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 2, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 3, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 4, 1) !~ '^[0-9]$')) OR (LENGTH(CAST(:NEW_THEME_NO AS TEXT)) = 5
    AND (SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 1, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 2, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 3, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 4, 1) !~ '^[0-9]$'
    OR SUBSTR(CAST(:NEW_THEME_NO AS TEXT), 5, 1) !~ '^[0-9]$')) OR (LENGTH(CAST(:NEW_THEME_NO AS TEXT)) <> 4
    AND LENGTH(CAST(:NEW_THEME_NO AS TEXT)) <> 5) THEN
        RAISE
    EXCEPTION
        'MDM_V_THEMES_IOF: This is not a valid Theme No';
    END IF;

    V_COUNTER := NULL;
    SELECT
        COUNT(T.THEME_NO) INTO V_COUNTER
    FROM
        (
            SELECT
                THEME_NO
            FROM
                GMD.V_THEMES
            UNION
            ALL
            SELECT
                THEME_NO
            FROM
                GMD.THEMES_ARCHIVE
        ) T
    WHERE
        T.THEME_NO = CAST(:NEW_THEME_NO AS TEXT);
    IF (V_COUNTER > 0) THEN
        RAISE
    EXCEPTION
        'MDM_V_THEMES_IOF: This Theme No already exists';
    END IF;

    V_COUNTER := NULL;
    V_D_REGISTRAT_DATE := CURRENT_DATE;
    IF (:NEW_OFFICIAL_IND = 'N') THEN
        RAISE
    EXCEPTION
        'MDM_V_THEMES_IOF: New Themes can only be inserted by Official Changes';
    END IF;

    IF (UPPER(:NEW_PORTF_PROJ_CD) = 'N') THEN
        IF (:NEW_THEME_DESC IS NULL
        OR LENGTH(:NEW_THEME_DESC) = 0) THEN
            RAISE
        EXCEPTION
            'MDM_V_THEMES_IOF: If Pharma Rx Portfolio Project is set to \"No\", then the Theme Description must be filled';
        END IF;
    END IF;

    IF (UPPER(:NEW_PORTF_PROJ_CD) = 'Y') AND (V_STATUS_CD <> 'C'
    OR :NEW_IN_PREP_IND = 'Y') THEN
        V_DESCRIPTION := GMD.GMD_UTIL_THEMES$GET_THEME_DESC_PORTFOLIO(
            P_THEME_NO_PORTF => NULL,
            P_MOLECULE_ID_PORTF => V_MOLECULE_ID,
            P_PROD_SHORT_CD_PORTF => :NEW_PROD_SHORT_CD,
            P_ODG_NO_PORT => V_ODG_NO,
            P_RESGRP_CD_PORT => V_RESGRP_CD,
            P_RESLIN_CD_PORT => V_RESLIN_CD,
            P_LINE_EXT_INFO_PORT => :NEW_LINE_EXT_INFO,
            P_IN_LIC_PRTNR_PORTF => V_MOLEC_IN_LIC_PRTNR,
            P_TRADEMARK_NO_PORTF => :NEW_TRADEMARK_NO,
            P_SHORT_NAME_PORTF => :NEW_SHORT_NAME,
            P_TRUNC_DESC_LENGTH => 'N'
        );
        IF (LENGTH(V_DESCRIPTION) > 90) THEN
            RAISE
        EXCEPTION
            'MDM_V_THEMES_IOF: The automatically generated Theme Description % is too long', V_DESCRIPTION;
        END IF;

        V_DESCRIPTION := TRIM(V_DESCRIPTION);
        V_PORTF_PROJ_CD := 'Y';
    ELSE
        V_DESCRIPTION := :NEW_THEME_DESC;
        V_PORTF_PROJ_CD := 'N';
    END IF;

    V_COUNTER := NULL;
    SELECT
        COUNT(T.THEME_NO) INTO V_COUNTER
    FROM
        GMD.V_THEMES T
    WHERE
        T.THEME_DESC = V_DESCRIPTION;
    IF (V_COUNTER > 0) THEN
        RAISE
    EXCEPTION
        'MDM_V_THEMES_IOF: This Theme Description already exists';
    END IF;

    V_COUNTER := NULL;
    V_VALID_TO := TO_DATE('09.09.9999', 'DD.MM.YYYY');
    V_SHORT_NAME := COALESCE(:NEW_MANUAL_SHORT_DESC, SUBSTR(V_DESCRIPTION, 1, 30));
    INSERT INTO GMD.THEMES(
        THEME_NO,
        REGISTRAT_DATE,
        ODG_NO,
        RESGRP_CD,
        RESLIN_CD,
        THEME_DESC,
        SHORT_NAME,
        STATUS_CD,
        DBA_CD,
        IN_PREP_IND,
        PROD_SHORT_CD,
        TRADEMARK_NO,
        BIO_ACTIVITY,
        APPLICANT,
        CONTACT,
        REGISTRAR,
        LINE_EXT_INFO,
        PORTF_PROJ_CD,
        CO_DEV_PRTNR,
        TECHNOLOGY_PRTNR,
        OFFICIAL_IND,
        CO_MAR_PRTNR,
        VALID_TO,
        PORTF_DA_GROUP_ID,
        MANUAL_SHORT_DESC,
        INS_USER,
        INS_DATE,
        UPD_USER,
        UPD_DATE
    ) VALUES (
        :NEW_THEME_NO,
        V_D_REGISTRAT_DATE,
        V_ODG_NO,
        V_RESGRP_CD,
        V_RESLIN_CD,
        COALESCE(V_DESCRIPTION, ''),
        V_SHORT_NAME,
        V_STATUS_CD,
        V_DBA_CD,
        :NEW_IN_PREP_IND,
        :NEW_PROD_SHORT_CD,
        CAST(NULLIF(CAST(:NEW_TRADEMARK_NO AS TEXT), '') AS NUMERIC),
        :NEW_BIO_ACTIVITY,
        :NEW_APPLICANT,
        :NEW_CONTACT,
        :INS_USER,
        :NEW_LINE_EXT_INFO,
        V_PORTF_PROJ_CD,
        :NEW_CO_DEV_PRTNR,
        :NEW_TECHNOLOGY_PRTNR,
        :NEW_OFFICIAL_IND,
        :NEW_CO_MAR_PRTNR,
        V_VALID_TO,
        CAST(NULLIF(CAST(:NEW_PORTF_DA_GROUP_ID AS TEXT), '') AS NUMERIC),
        :NEW_MANUAL_SHORT_DESC,
        :INS_USER,
        :INS_DATE,
        NULL,
        NULL
    );
    IF :NEW_MOLECULE_ID IS NOT NULL THEN
        INSERT INTO GMD.THEME_MOLECULE_MAP(
            THEME_NO,
            MOLECULE_ID,
            MOLECULE_SEQ_NO,
            VALID_IND,
            INS_USER,
            INS_DATE
        ) VALUES (
            :NEW_THEME_NO,
            COALESCE(V_MOLECULE_ID, ''),
            1,
            'Y',
            :INS_USER,
            :INS_DATE
        );
    END IF;

    IF (:NEW_PROPOSAL_ID IS NOT NULL) THEN
        SELECT
            COUNT() INTO V_EVOLVED_NMP_CNT
        FROM
            PREDMD.NEW_MEDICINE_PROPOSALS
        WHERE
            PROPOSAL_ID = CAST(NULLIF(CAST(:NEW_PROPOSAL_ID AS TEXT), '') AS NUMERIC)
            AND PROPOSAL_STATUS_CD = 'E';
        IF (V_EVOLVED_NMP_CNT = 0) THEN
            UPDATE PREDMD.NEW_MEDICINE_PROPOSALS
            SET
                PROPOSAL_STATUS_CD = 'E',
                EVOLVED_THEME_NO = :NEW_THEME_NO,
                PROPOSAL_NAME = V_SHORT_NAME,
                REASON_FOR_CHANGE = '* Automatic update of proposal_name after short_name change in evolved theme *',
                UPD_USER= :UPD_USER,
                UPD_DATE= :UPD_DATE
            WHERE
                PROPOSAL_ID = CAST(NULLIF(CAST(:NEW_PROPOSAL_ID AS TEXT), '') AS NUMERIC);
        END IF;
    END IF;

    IF (:NEW_THEME_NO IS NOT NULL
    AND GMD.GMD_UTIL_THEMES$GET_THEMES_RANGE_AUTOMATIC_NMP(CAST(:NEW_THEME_NO AS TEXT)) = 'Y') THEN
        IF :NEW_PROPOSAL_ID IS NOT NULL THEN
            SELECT
                COUNT() INTO V_EVOLVED_NMP_CNT
            FROM
                PREDMD.NEW_MEDICINE_PROPOSALS
            WHERE
                PROPOSAL_ID = CAST(NULLIF(CAST(:NEW_PROPOSAL_ID AS TEXT), '') AS NUMERIC)
                AND PROPOSAL_NAME = V_SHORT_NAME
                AND PROPOSAL_STATUS_CD = 'E';
        END IF;

        IF :NEW_PROPOSAL_ID IS NULL OR (:NEW_PROPOSAL_ID IS NOT NULL
        AND V_EVOLVED_NMP_CNT = 0) THEN
            IF (:NEW_MOLECULE_ID IS NOT NULL) THEN
                BEGIN
                    SELECT
                        PHARMACOLOGICAL_TYPE_ID,
                        MOLECULE_TYPE_ID INTO V_PHARMACOLOGICAL_TYPE_ID,
                        V_MOLECULE_TYPE_ID
                    FROM
                        GMD.V_THEME_MOLECULES_MRHUB M
                        LEFT JOIN MDMAPPL.MDM_V_PRODUCT_FAMILIES B
                        ON M.PRODUCT_FAMILY_CD = B.PRODUCT_FAMILY_CD
                    WHERE
                        M.VALID_IND = 'Y'
                        AND MOLECULE_ID = CAST(NULLIF(CAST(:NEW_MOLECULE_ID AS TEXT), '') AS NUMERIC);
                EXCEPTION
                    WHEN OTHERS THEN
                        RAISE EXCEPTION 'MDM_V_THEMES_IOF: This is not a valid Molecule ID';
                END;
            END IF;

            INSERT INTO PREDMD.NEW_MEDICINE_PROPOSALS (
                PROPOSAL_STATUS_CD,
                EVOLVED_THEME_NO,
                PROPOSAL_NAME,
                PHARMACOLOGICAL_TYPE_ID,
                MOLECULE_TYPE_ID,
                REASON_FOR_CHANGE,
                INS_USER,
                INS_DATE
            ) VALUES (
                'E',
                :NEW_THEME_NO,
                V_SHORT_NAME,
                COALESCE(V_PHARMACOLOGICAL_TYPE_ID, C_PHARMACOLOGICAL_TYPE_ID),
                COALESCE(V_MOLECULE_TYPE_ID, C_MOLECULE_TYPE_ID),
                '* Automatic creation of nmp for early development themes *',
                :INS_USER,
                :INS_DATE
            );
        END IF;
    END IF;

    BEGIN
        FOR I1 IN (
            SELECT
                A.THEME_NO,
                A.REGISTRAT_DATE
            FROM
                GMD.V_THEMES A
            WHERE
                A.VALID_TO <= CURRENT_DATE
        ) LOOP
            DELETE FROM GMD.THEMES
            WHERE
                THEME_NO = I1.THEME_NO
                AND REGISTRAT_DATE = I1.REGISTRAT_DATE;
        END LOOP;
    END;
END $$;