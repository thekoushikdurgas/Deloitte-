DECLARE
   INVALID_THEME_NO EXCEPTION;
   DELETE_NO_MORE_POSSIBLE EXCEPTION;
   THEME_NO_ONLY_INSERT EXCEPTION;
   DESCRIPTION_TOO_LONG EXCEPTION;
   THEME_DESC_PROPOSAL_TOO_LONG EXCEPTION;
   THEME_DESC_ALT_TOO_LONG EXCEPTION;
   THEME_NO_CANNOT_BE_INSERTED EXCEPTION;
   ONLYONEOFFICIALCHANGEPERDAY EXCEPTION;
   INSERTSMUSTBEOFFICIAL EXCEPTION;
   THEMEDESCRIPTIONMANDATORY EXCEPTION;
   THEME_DESC_NOT_UNIQUE EXCEPTION;
   IN_PREP_NOT_PORTF_PROJ EXCEPTION;
   IN_PREP_NOT_CLOSED EXCEPTION;
   INVALID_MOLECULE_ID EXCEPTION;
   SEC_MOL_LIST_NOT_EMPTY EXCEPTION;
   ADMIN_UPDATE_ONLY EXCEPTION;
   PORTF_PROJ_MOL_CRE_ERR EXCEPTION;
   DEBUGGING EXCEPTION;
   V_COUNTER                    PLS_INTEGER;
   V_CODE                       VARCHAR2(2);
   V_ODG_NO                     VARCHAR2(2);
   V_RESGRP_CD                  VARCHAR2(2);
   V_RESLIN_CD                  VARCHAR2(2);
   V_STATUS_CD                  VARCHAR2(1);
   V_DBA_CD                     PLS_INTEGER;
   V_PORTF_PROJ_CD              VARCHAR2(1);
   V_DESCRIPTION                VARCHAR2(500);
   V_RESLIN_DESC                VARCHAR2(60);
   V_THEME_DESC_LENGTH          PLS_INTEGER;
   V_D_REGISTRAT_DATE           DATE;
   V_D_INS_DATE                 DATE;
   V_FUTURE_REGISTRAT           DATE;
   V_VALID_TO                   DATE;
   V_USERID                     VARCHAR2(30);
   V_IS_ADMIN_CNT               SIMPLE_INTEGER := 0;
   V_SEC_MOL_CNT                SIMPLE_INTEGER := 0;
   V_MOLECULE_ID                VARCHAR2(5) := NULL;
   V_MOLECULE_RG_NO             VARCHAR2(20) := NULL;
   V_MOLEC_IN_LIC_PRTNR         VARCHAR2(15) := NULL;
   V_NEW_RG_NO                  V_THEME_MOLECULES.RG_NO%TYPE;
   V_COMPARATOR_IND             V_THEME_MOLECULES.COMPARATOR_IND%TYPE;
   V_THEME_DESC_PROPOSAL        MDM_V_THEMES_MTN.THEME_DESC_PROPOSAL%TYPE;
   V_SHORT_NAME                 VARCHAR2(30);
   C_MOLECULE_TYPE_ID           CONSTANT V_MOLECULE_TYPES.MOLECULE_TYPE_ID%TYPE := 99; -- Other Program
   C_PHARMACOLOGICAL_TYPE_ID    CONSTANT V_PHARMACOLOGICAL_TYPES.PHARMACOLOGICAL_TYPE_ID%TYPE := 19; -- Unknown
   V_EVOLVED_NMP_CNT            PLS_INTEGER;
   V_TRADEMARK_NO               V_THEMES.TRADEMARK_NO%TYPE;
   V_MOLECULE_TYPE_ID           V_MOLECULE_TYPES.MOLECULE_TYPE_ID%TYPE;
   V_PHARMACOLOGICAL_TYPE_ID    V_PHARMACOLOGICAL_TYPES.PHARMACOLOGICAL_TYPE_ID%TYPE;
BEGIN
 
   -- check user
   SELECT
      NVL(TXO_SECURITY.GET_USERID, USER) INTO V_USERID
   FROM
      DUAL;
 
   -- v_is_admin_cnt = 0 => is NOT a full admin user (MDMS_THEME_ADMIN_FULL_ACCESS)
   -- v_is_admin_cnt > 0 => is a full admin user (MDMS_THEME_ADMIN_FULL_ACCESS)
   SELECT
      COUNT(*) INTO V_IS_ADMIN_CNT
   FROM
      TXO_USERS_ROLES_MAP
   WHERE
      ROLE_ID IN (315)
      AND USERID = V_USERID;
 
   -- find next free rg_no which may be used later in this trigger :
   SELECT
      NEW_RG_NO INTO V_NEW_RG_NO
   FROM
      (
         SELECT
            NEW_RG_NO
         FROM
            (
               SELECT
                  ROWNUM AS NEW_RG_NO
               FROM
                  DUAL
               CONNECT BY
                  1 = 1
                  AND ROWNUM <= 6999
            )                 
         WHERE
            NEW_RG_NO > 5999 MINUS
            SELECT
               TO_NUMBER(RG_NO)
            FROM
               V_THEME_MOLECULES
      )                 
   WHERE
      ROWNUM = 1;
   IF (:NEW.IN_PREP_IND = 'Y') THEN
      IF (:NEW.PORTF_PROJ_CD <> 'Y') THEN
         RAISE IN_PREP_NOT_PORTF_PROJ;
      END IF;

      IF (:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0) THEN
         RAISE IN_PREP_NOT_CLOSED;
      END IF;

      IF (:NEW.MOLECULE_ID IS NULL) THEN
         TXO_UTIL.SET_WARNING('No Molecule assigned to In-Prep Theme ' || :NEW.THEME_NO || '!');
      END IF;
   END IF;
 

   -- set THEME_MOLECULE RG Number for first assignment of molecule
   IF (:NEW.MOLECULE_ID IS NOT NULL) THEN
      BEGIN
         SELECT
            RG_NO,
            M.COMPARATOR_IND INTO V_MOLECULE_RG_NO,
            V_COMPARATOR_IND
         FROM
            V_THEME_MOLECULES M
         WHERE
            MOLECULE_ID = :NEW.MOLECULE_ID
            AND M.VALID_IND = 'Y';
      EXCEPTION
         WHEN NO_DATA_FOUND THEN
            RAISE INVALID_MOLECULE_ID;
      END;

      IF (V_MOLECULE_RG_NO IS NULL) THEN
         IF (V_COMPARATOR_IND = 'Y') THEN
            NULL; -- no RG_NO for Comparators -----------------------------
         ELSE --   for Roche molecules ----------------------------------
            -- first time assignment as RG_NO is empty.
            -- set RG_NO to RG + first theme_no the molecule was ever assigned to
            UPDATE V_THEME_MOLECULES
            SET
               RG_NO = V_NEW_RG_NO --:new.theme_no
            WHERE
               MOLECULE_ID = :NEW.MOLECULE_ID;
         END IF;
      END IF;
   END IF;
 

   -- RAISE debugging;
   -- The Parameter :NEW.RESLIN_DESC_CONCAT consists of 4 fields
   V_ODG_NO := SUBSTR(:NEW.RESLIN_DESC_CONCAT, 1, 2);
   V_RESGRP_CD := SUBSTR(:NEW.RESLIN_DESC_CONCAT, 4, 2);
   V_RESLIN_CD := SUBSTR(:NEW.RESLIN_DESC_CONCAT, 7, 2);
   V_RESLIN_DESC := SUBSTR(:NEW.RESLIN_DESC_CONCAT, 12, LENGTH(:NEW.RESLIN_DESC_CONCAT));
   IF (:NEW.STATUS_DESC IS NOT NULL) THEN
      SELECT
         STATUS_CD INTO V_STATUS_CD
      FROM
         MDM_V_THEME_STATUS
      WHERE
         STATE_DESC = :NEW.STATUS_DESC;
   ELSE
      V_STATUS_CD := NULL;
   END IF;

   IF (:NEW.DBA_DESC_CONCAT IS NOT NULL) THEN
      SELECT
         DBA_CD INTO V_DBA_CD
      FROM
         MDM_V_DISEASE_BIOLOGY_AREAS
      WHERE
         DBA_SHORT_DESC
         || ' - '
         || DBA_DESC = :NEW.DBA_DESC_CONCAT;
   ELSE
      V_DBA_CD := NULL;
   END IF;

   V_MOLEC_IN_LIC_PRTNR := GMD_UTIL_THEMES.GET_MOLEC_IN_LIC_PRTNR(:NEW.MOLECULE_ID);
   IF (:NEW.OFFICIAL_IND = 'N') THEN
      V_TRADEMARK_NO := :NEW.TRADEMARK_NO;
   ELSE
      V_TRADEMARK_NO := :OLD.TRADEMARK_NO;
   END IF;

   V_THEME_DESC_PROPOSAL := GMD_UTIL_THEMES.GET_THEME_SHORT_NAME(P_THEME_NO_PORTF => :NEW.THEME_NO, P_MOLECULE_ID_PORTF => :NEW.MOLECULE_ID, P_PROD_SHORT_CD_PORTF => :NEW.PROD_SHORT_CD, P_ODG_NO_PORT => V_ODG_NO, P_RESGRP_CD_PORT => V_RESGRP_CD, P_RESLIN_CD_PORT => V_RESLIN_CD, P_LINE_EXT_INFO_PORT => :NEW.LINE_EXT_INFO, P_IN_LIC_PRTNR_PORTF => NULL, P_TRADEMARK_NO_PORTF => V_TRADEMARK_NO, P_TRUNC_DESC_LENGTH => 'N');
   IF (:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30) THEN
      RAISE THEME_DESC_PROPOSAL_TOO_LONG;
   END IF;

   V_SHORT_NAME := COALESCE(:NEW.MANUAL_SHORT_DESC, V_THEME_DESC_PROPOSAL);
   IF (INSERTING) THEN
      IF (:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0) THEN
         RAISE ADMIN_UPDATE_ONLY;
      END IF;
 

      -- CMA 1685, automatic molecule creation
      -- CMA 1820, add RG_NO to inserted values
      V_MOLECULE_ID := :NEW.MOLECULE_ID;
      IF (:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL) THEN
         IF (NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL) THEN
            RAISE PORTF_PROJ_MOL_CRE_ERR;
         ELSE
            INSERT INTO MDM_V_THEME_MOLECULES_MTN(
               MOLECULE_DESC,
               VALID_IND,
               RG_NO,
               CANCER_IMMUNOTHERAPY_IND,
               MOLECULE_TYPE_ID,
               PHARMACOLOGICAL_TYPE_ID
            ) VALUES (
               NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL),
               'Y',
               V_NEW_RG_NO,
               'N',
               C_MOLECULE_TYPE_ID,
               C_PHARMACOLOGICAL_TYPE_ID
            );
            SELECT
               MOLECULE_ID INTO V_MOLECULE_ID
            FROM
               V_THEME_MOLECULES
            WHERE
               MOLECULE_DESC = NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL)
               AND VALID_IND = 'Y'
               AND RG_NO = V_NEW_RG_NO
               AND CANCER_IMMUNOTHERAPY_IND = 'N'
               AND MOLECULE_TYPE_ID = C_MOLECULE_TYPE_ID
               AND PHARMACOLOGICAL_TYPE_ID = C_PHARMACOLOGICAL_TYPE_ID;
 
            --  create molecule mapping (Primary Molecule)
            INSERT INTO THEME_MOLECULE_MAP TMMAP(
               TMMAP.THEME_NO,
               TMMAP.MOLECULE_ID,
               TMMAP.MOLECULE_SEQ_NO,
               TMMAP.VALID_IND
            ) VALUES (
               :NEW.THEME_NO,
               V_MOLECULE_ID,
               1,
               'Y'
            ); -- primary molecule!
         END IF;
      END IF;

      CASE LENGTH(:NEW.THEME_NO)
         WHEN 4 THEN
            IF (SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9) THEN
               RAISE INVALID_THEME_NO;
            END IF;
         WHEN 5 THEN
            IF (SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9) THEN
               RAISE INVALID_THEME_NO;
            END IF;
         ELSE
            RAISE INVALID_THEME_NO;
      END CASE;

      V_COUNTER := NULL;
 
      -- Is this theme_no really new?
      SELECT
         COUNT(T.THEME_NO) INTO V_COUNTER
      FROM
         (
            SELECT
               THEME_NO
            FROM
               V_THEMES
            UNION
            ALL
            SELECT
               THEME_NO
            FROM
               GMD.THEMES_ARCHIVE
         )                  T
      WHERE
         T.THEME_NO = :NEW.THEME_NO;
      IF (V_COUNTER > 0) THEN
         RAISE THEME_NO_CANNOT_BE_INSERTED;
      END IF;

      V_COUNTER := NULL;
      V_D_REGISTRAT_DATE := SYSDATE;
 
      -- VERIFY OFFICIAL-IND --------------------------
      IF (:NEW.OFFICIAL_IND = 'N') THEN
         RAISE INSERTSMUSTBEOFFICIAL;
      END IF;

      IF (UPPER(:NEW.PORTF_PROJ_CD) = 'N') THEN
         IF (:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0) THEN
            RAISE THEMEDESCRIPTIONMANDATORY;
         END IF;
      END IF;
 

      -- The Theme Description is generated automatically
      IF (UPPER(:NEW.PORTF_PROJ_CD) = 'Y') THEN
         V_DESCRIPTION := GMD.GMD_UTIL_THEMES.GET_THEME_DESC_PORTFOLIO(
            P_THEME_NO_PORTF => NULL,
            P_MOLECULE_ID_PORTF => V_MOLECULE_ID,
            P_PROD_SHORT_CD_PORTF => :NEW.PROD_SHORT_CD,
            P_ODG_NO_PORT => V_ODG_NO,
            P_RESGRP_CD_PORT => V_RESGRP_CD,
            P_RESLIN_CD_PORT => V_RESLIN_CD,
            P_LINE_EXT_INFO_PORT => :NEW.LINE_EXT_INFO,
            P_IN_LIC_PRTNR_PORTF => V_MOLEC_IN_LIC_PRTNR,
            P_TRADEMARK_NO_PORTF => :NEW.TRADEMARK_NO,
            P_SHORT_NAME_PORTF => :NEW.SHORT_NAME,
            P_TRUNC_DESC_LENGTH => 'N'
         );
         IF (LENGTH(V_DESCRIPTION) > 90) THEN
            RAISE DESCRIPTION_TOO_LONG;
         END IF;

         V_DESCRIPTION := TRIM(V_DESCRIPTION);
         V_PORTF_PROJ_CD := 'Y';
      ELSE
 
         -- The given Theme Description is inserted
         V_DESCRIPTION := :NEW.THEME_DESC;
         V_PORTF_PROJ_CD := 'N';
      END IF; -- :NEW.PORTF_PROJ_CD = 'Y'
      -- NOW VERIFY UNIQUENESS OF THEME_DESC --------------
      V_COUNTER := NULL;
      SELECT
         COUNT(T.THEME_NO) INTO V_COUNTER
      FROM
         V_THEMES T
      WHERE
         T.THEME_DESC = V_DESCRIPTION;
      IF (V_COUNTER > 0) THEN
         RAISE THEME_DESC_NOT_UNIQUE;
      END IF;

      V_COUNTER := NULL;
      V_VALID_TO := TO_DATE('09.09.9999', 'DD.MM.YYYY');
      V_SHORT_NAME := NVL(:NEW.MANUAL_SHORT_DESC, SUBSTR(V_DESCRIPTION, 1, 30));
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
         MANUAL_SHORT_DESC
      ) VALUES (
         :NEW.THEME_NO,
         V_D_REGISTRAT_DATE,
         V_ODG_NO,
         V_RESGRP_CD,
         V_RESLIN_CD,
         V_DESCRIPTION,
         V_SHORT_NAME,
         V_STATUS_CD,
         V_DBA_CD,
         :NEW.IN_PREP_IND,
         :NEW.PROD_SHORT_CD,
         :NEW.TRADEMARK_NO,
         :NEW.BIO_ACTIVITY,
         :NEW.APPLICANT,
         :NEW.CONTACT,
         TXO_UTIL.GET_USERID,
         :NEW.LINE_EXT_INFO,
         V_PORTF_PROJ_CD,
         :NEW.CO_DEV_PRTNR,
         :NEW.TECHNOLOGY_PRTNR,
         :NEW.OFFICIAL_IND,
         :NEW.CO_MAR_PRTNR,
         V_VALID_TO,
         :NEW.PORTF_DA_GROUP_ID,
         :NEW.MANUAL_SHORT_DESC
      );
      IF (:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL) THEN
 
         -- handle primary molecule mapping to this theme
         INSERT INTO MDM_V_THEME_MOLECULE_MAP_MTN A(
            A.THEME_NO,
            A.MOLECULE_ID,
            A.MOLECULE_SEQ_NO,
            A.VALID_IND
         ) VALUES (
            :NEW.THEME_NO,
            V_MOLECULE_ID,
            1,
            'Y'
         ); --(PRIMARY, molecule_seq_no = 1)
      END IF;
 

      -- End Code  for Inserting
   ELSIF (UPDATING) THEN
 
      -- check admin access (role 315)
      IF (:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0 THEN
         RAISE ADMIN_UPDATE_ONLY;
      END IF;

      IF (:NEW.THEME_NO <> :OLD.THEME_NO) THEN
         RAISE THEME_NO_ONLY_INSERT;
      END IF;
 

      -- CMA 1544 Registrat_date is
      --   * always sysdate for official updates
      --   * always :OLD.registrat_date for inofficial updates
      IF (:NEW.OFFICIAL_IND = 'N') THEN
 
         -- inofficial => do not change registrat_date
         V_D_REGISTRAT_DATE := TO_DATE(:OLD.REGISTRAT_DATE, 'dd-mm-yyyy');
      ELSE -- it is an official change
         -- official change => registrat_date will be set to sysdate
         V_D_REGISTRAT_DATE := SYSDATE;
      END IF;

      IF (UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD) THEN
         V_DESCRIPTION := GMD.GMD_UTIL_THEMES.GET_THEME_DESC_PORTFOLIO(
            P_THEME_NO_PORTF => :NEW.THEME_NO,
            P_MOLECULE_ID_PORTF => :NEW.MOLECULE_ID,
            P_PROD_SHORT_CD_PORTF => :NEW.PROD_SHORT_CD,
            P_ODG_NO_PORT => V_ODG_NO,
            P_RESGRP_CD_PORT => V_RESGRP_CD,
            P_RESLIN_CD_PORT => V_RESLIN_CD,
            P_LINE_EXT_INFO_PORT => :NEW.LINE_EXT_INFO,
            P_IN_LIC_PRTNR_PORTF => V_MOLEC_IN_LIC_PRTNR,
            P_TRADEMARK_NO_PORTF => :NEW.TRADEMARK_NO,
            P_SHORT_NAME_PORTF => :NEW.SHORT_NAME,
            P_TRUNC_DESC_LENGTH => 'N'
         );
         V_DESCRIPTION := TRIM(V_DESCRIPTION);
         V_PORTF_PROJ_CD := 'Y';
      ELSE
         IF (:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0) THEN
            RAISE THEMEDESCRIPTIONMANDATORY;
         ELSE
            V_DESCRIPTION := :NEW.THEME_DESC;
            V_PORTF_PROJ_CD := :NEW.PORTF_PROJ_CD;
         END IF;
      END IF;

      IF (LENGTH(V_DESCRIPTION) > 90) THEN
         RAISE DESCRIPTION_TOO_LONG;
      END IF;
 

      -- NOW VERIFY UNIQUENESS OF THEME_DESC --------------
      --(but not within the same theme_no, then is no uniqueness required)
      V_COUNTER := NULL;
      SELECT
         COUNT(T.THEME_NO) INTO V_COUNTER
      FROM
         V_THEMES T
      WHERE
         T.THEME_DESC = V_DESCRIPTION
         AND T.THEME_NO <> :NEW.THEME_NO;
      IF (V_COUNTER > 0) THEN
         RAISE THEME_DESC_NOT_UNIQUE;
      END IF;

      V_COUNTER := NULL;
 
      --  Code for INOFFICIAL Changes
      IF (:NEW.OFFICIAL_IND = 'N') THEN
         UPDATE GMD.THEMES
         SET
            ODG_NO = V_ODG_NO,
            RESGRP_CD = V_RESGRP_CD,
            RESLIN_CD = V_RESLIN_CD,
            THEME_DESC = V_DESCRIPTION,
            SHORT_NAME = V_SHORT_NAME,
            STATUS_CD = V_STATUS_CD,
            DBA_CD = V_DBA_CD,
            IN_PREP_IND = :NEW.IN_PREP_IND,
            PROD_SHORT_CD = :NEW.PROD_SHORT_CD,
            TRADEMARK_NO = :NEW.TRADEMARK_NO,
            BIO_ACTIVITY = :NEW.BIO_ACTIVITY,
            APPLICANT = :NEW.APPLICANT,
            CONTACT = :NEW.CONTACT,
            LINE_EXT_INFO = :NEW.LINE_EXT_INFO,
            PORTF_PROJ_CD = V_PORTF_PROJ_CD,
            CO_DEV_PRTNR = :NEW.CO_DEV_PRTNR,
            TECHNOLOGY_PRTNR = :NEW.TECHNOLOGY_PRTNR,
            OFFICIAL_IND = :NEW.OFFICIAL_IND,
            CO_MAR_PRTNR = :NEW.CO_MAR_PRTNR,
            PORTF_DA_GROUP_ID = :NEW.PORTF_DA_GROUP_ID,
            MANUAL_SHORT_DESC = :NEW.MANUAL_SHORT_DESC
         WHERE
            THEME_NO = :NEW.THEME_NO
            AND TO_DATE(REGISTRAT_DATE, 'DD-MM-YYYY') = V_D_REGISTRAT_DATE;
      ELSE
 
         -- Code for OFFICIAL changes  :NEW.OFFICIAL_IND = 'Y'
         -- then this is  the first and only record for this registrat-date
         V_COUNTER := NULL;
 
         -- only one official change allowed per day
         SELECT
            COUNT(*) INTO V_COUNTER
         FROM
            V_THEMES T
         WHERE
            TRUNC(T.REGISTRAT_DATE) = TRUNC(SYSDATE)
            AND T.THEME_NO = :NEW.THEME_NO;
         IF (V_COUNTER > 0) THEN
            RAISE ONLYONEOFFICIALCHANGEPERDAY;
         END IF;

         V_COUNTER := NULL;
         UPDATE GMD.THEMES
         SET
            ODG_NO = V_ODG_NO,
            RESGRP_CD = V_RESGRP_CD,
            RESLIN_CD = V_RESLIN_CD,
            THEME_DESC = V_DESCRIPTION,
            SHORT_NAME = V_SHORT_NAME,
            STATUS_CD = V_STATUS_CD,
            DBA_CD = V_DBA_CD,
            IN_PREP_IND = :NEW.IN_PREP_IND,
            PROD_SHORT_CD = :NEW.PROD_SHORT_CD,
            TRADEMARK_NO = :NEW.TRADEMARK_NO,
            BIO_ACTIVITY = :NEW.BIO_ACTIVITY,
            APPLICANT = :NEW.APPLICANT,
            CONTACT = :NEW.CONTACT,
            LINE_EXT_INFO = :NEW.LINE_EXT_INFO,
            PORTF_PROJ_CD = V_PORTF_PROJ_CD,
            CO_DEV_PRTNR = :NEW.CO_DEV_PRTNR,
            TECHNOLOGY_PRTNR = :NEW.TECHNOLOGY_PRTNR,
            OFFICIAL_IND = :NEW.OFFICIAL_IND,
            CO_MAR_PRTNR = :NEW.CO_MAR_PRTNR,
            REGISTRAT_DATE = SYSDATE,
            REGISTRAR = V_USERID,
            PORTF_DA_GROUP_ID = :NEW.PORTF_DA_GROUP_ID,
            MANUAL_SHORT_DESC = :NEW.MANUAL_SHORT_DESC
         WHERE
            THEME_NO = :NEW.THEME_NO;
      END IF;
 

      -- handle primary molecule mapping to this theme
      -- this code is identical for official and in-official changes
      CASE
         WHEN :OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL THEN
 
         -- insert a new mapping (PRIMARY, molecule_seq_no = 1)
            INSERT INTO MDM_V_THEME_MOLECULE_MAP_MTN A(
               A.THEME_NO,
               A.MOLECULE_ID,
               A.MOLECULE_SEQ_NO,
               A.VALID_IND
            ) VALUES (
               :NEW.THEME_NO,
               :NEW.MOLECULE_ID,
               1,
               'Y'
            );
         WHEN :OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL THEN
 
         -- update an existing mapping (PRIMARY, molecule_seq_no = 1)
            UPDATE MDM_V_THEME_MOLECULE_MAP A
            SET
               A.MOLECULE_ID = :NEW.MOLECULE_ID,
               A.VALID_IND = 'Y'
            WHERE
               A.THEME_NO = :NEW.THEME_NO
               AND A.MOLECULE_SEQ_NO = 1
               AND A.VALID_IND = 'Y';
         WHEN :OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL THEN
            SELECT
               COUNT(*) INTO V_SEC_MOL_CNT
            FROM
               MDM_V_THEME_MOLECULE_MAP_MTN A
            WHERE
               A.THEME_NO = :NEW.THEME_NO
               AND A.MOLECULE_SEQ_NO > 1
               AND A.VALID_IND = 'Y';
            IF (V_SEC_MOL_CNT > 0) THEN
               RAISE SEC_MOL_LIST_NOT_EMPTY; -- error
            ELSE
 
               -- soft-delete an existing mapping (PRIMARY, molecule_seq_no = 1)
               UPDATE MDM_V_THEME_MOLECULE_MAP A
               SET
                  A.VALID_IND = 'N'
               WHERE
                  A.MOLECULE_ID = :OLD.MOLECULE_ID
                  AND A.THEME_NO = :NEW.THEME_NO
                  AND A.MOLECULE_SEQ_NO = 1
                  AND A.VALID_IND = 'Y';
            END IF;
         ELSE
            NULL;
      END CASE;
   ELSIF (DELETING) THEN
      IF ((:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0) THEN
         RAISE ADMIN_UPDATE_ONLY;
      END IF;
 

      -- deleting is only possible, if theme_no has been
      -- inserted on the same day
      -- only if this change has been
      IF (TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)) THEN
         DELETE FROM GMD.THEMES A
         WHERE
            A.THEME_NO = :OLD.THEME_NO
            AND TRUNC(A.REGISTRAT_DATE) = TRUNC(SYSDATE);
      ELSE
         RAISE DELETE_NO_MORE_POSSIBLE;
      END IF;
   END IF;
 

   --  Code for Inserting, Updating, Deleting
   IF (INSERTING OR UPDATING) THEN
      IF (:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL) THEN
 
         -- check if the entered NMP is evolved
         SELECT
            COUNT(*) INTO V_EVOLVED_NMP_CNT
         FROM
            MDM_V_NEW_MEDICINE_PROPOSALS_MTN
         WHERE
            PROPOSAL_ID = :NEW.PROPOSAL_ID
            AND PROPOSAL_STATUS_CD = 'E';
 
         ----------
         -- if the proposal id is set and the NMP is not evolved then update the corresponding
         -- New Medicinie Proposal status to evolved
         IF (V_EVOLVED_NMP_CNT = 0) THEN
            UPDATE MDM_V_NEW_MEDICINE_PROPOSALS_MTN
            SET
               PROPOSAL_STATUS_CD = 'E',
               EVOLVED_THEME_NO = :NEW.THEME_NO,
               PROPOSAL_NAME = V_SHORT_NAME,
               REASON_FOR_CHANGE = '** Automatic update of proposal_name after short_name change in evolved theme **'
            WHERE
               PROPOSAL_ID = :NEW.PROPOSAL_ID;
         END IF;
      ELSE
         IF (:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL) THEN
            UPDATE MDM_V_NEW_MEDICINE_PROPOSALS_MTN
            SET
               PROPOSAL_STATUS_CD = 'A',
               EVOLVED_THEME_NO = NULL
            WHERE
               PROPOSAL_ID = :OLD.PROPOSAL_ID;
         ELSE
            IF (:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID) THEN
 
               -- set to Active the old New Medicine Proposal
               UPDATE MDM_V_NEW_MEDICINE_PROPOSALS_MTN
               SET
                  PROPOSAL_STATUS_CD = 'A',
                  EVOLVED_THEME_NO = NULL
               WHERE
                  PROPOSAL_ID = :OLD.PROPOSAL_ID;
 
               -- set to Evolved the new choosen New Medicine Proposal
               UPDATE MDM_V_NEW_MEDICINE_PROPOSALS_MTN
               SET
                  PROPOSAL_STATUS_CD = 'E',
                  EVOLVED_THEME_NO = :NEW.THEME_NO,
                  PROPOSAL_NAME = V_SHORT_NAME,
                  REASON_FOR_CHANGE = '** Automatic update of proposal_name after short_name change in evolved theme **'
               WHERE
                  PROPOSAL_ID = :NEW.PROPOSAL_ID;
            END IF;
         END IF;
      END IF;
 

      -- short_name update
      IF (NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')) THEN
 
         -- check if this is an evolved proposal
         SELECT
            COUNT(*) INTO V_EVOLVED_NMP_CNT
         FROM
            MDM_V_NEW_MEDICINE_PROPOSALS_MTN NMP
         WHERE
            NMP.EVOLVED_THEME_NO =:NEW.THEME_NO
            AND NMP.PROPOSAL_STATUS_CD = 'E';
         IF (V_EVOLVED_NMP_CNT > 0) THEN
 
            -- short_name has changed so proposal_name must be updated accordingly
            UPDATE MDM_V_NEW_MEDICINE_PROPOSALS_MTN NMP
            SET
               NMP.PROPOSAL_NAME = V_SHORT_NAME,
               NMP.REASON_FOR_CHANGE = '** Automatic update of proposal_name after short_name change in evolved theme **'
            WHERE
               NMP.EVOLVED_THEME_NO =:NEW.THEME_NO
               AND NMP.PROPOSAL_STATUS_CD = 'E';
         END IF;
      END IF;
   END IF;
 

   -- handle New Medicine Proposals with theme_no starting with 71.. or 74
   IF (INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y') THEN
      IF (:NEW.PROPOSAL_ID IS NOT NULL) THEN
         SELECT
            COUNT(*) INTO V_EVOLVED_NMP_CNT
         FROM
            MDM_V_NEW_MEDICINE_PROPOSALS_MTN
         WHERE
            PROPOSAL_ID = :NEW.PROPOSAL_ID
            AND PROPOSAL_NAME = V_SHORT_NAME
            AND PROPOSAL_STATUS_CD = 'E';
      END IF;
 

      -- automatic create NMP only if no prposal_id is selected or the selected one is evolved
      IF (:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)) THEN
         IF (:NEW.MOLECULE_ID IS NOT NULL) THEN
            BEGIN
               SELECT
                  PHARMACOLOGICAL_TYPE_ID,
                  MOLECULE_TYPE_ID INTO V_PHARMACOLOGICAL_TYPE_ID,
                  V_MOLECULE_TYPE_ID
               FROM
                  V_THEME_MOLECULES M
               WHERE
                  MOLECULE_ID = :NEW.MOLECULE_ID
                  AND M.VALID_IND = 'Y';
            EXCEPTION
               WHEN NO_DATA_FOUND THEN
                  RAISE INVALID_MOLECULE_ID;
            END;
         END IF;

         INSERT INTO MDM_V_NEW_MEDICINE_PROPOSALS_MTN (
            PROPOSAL_STATUS_CD,
            EVOLVED_THEME_NO,
            PROPOSAL_NAME,
            PHARMACOLOGICAL_TYPE_ID,
            MOLECULE_TYPE_ID,
            REASON_FOR_CHANGE
         ) VALUES (
            'E',
            :NEW.THEME_NO,
            V_SHORT_NAME,
            NVL(V_PHARMACOLOGICAL_TYPE_ID, C_PHARMACOLOGICAL_TYPE_ID),
            NVL(V_MOLECULE_TYPE_ID, C_MOLECULE_TYPE_ID),
            '** Automatic creation of nmp for early development themes **'
         );
      END IF;
   END IF;

   BEGIN
 
      -- set variable
      -- is_from_theme_validity_check := TRUE;
      FOR I1 IN (
         SELECT
            A.THEME_NO,
            A.REGISTRAT_DATE
         FROM
            V_THEMES A
         WHERE
            A.VALID_TO <= TRUNC(SYSDATE)
      ) LOOP
         DELETE FROM GMD.THEMES
         WHERE
            THEME_NO = I1.THEME_NO
            AND REGISTRAT_DATE = I1.REGISTRAT_DATE;
      END LOOP;
   END;
EXCEPTION
   WHEN ADMIN_UPDATE_ONLY THEN
      RAISE_APPLICATION_ERROR(-20115, 'MDM_V_THEMES_IOF');
   WHEN IN_PREP_NOT_PORTF_PROJ THEN
      RAISE_APPLICATION_ERROR(-20116, 'MDM_V_THEMES_IOF');
   WHEN IN_PREP_NOT_CLOSED THEN
      RAISE_APPLICATION_ERROR(-20117, 'MDM_V_THEMES_IOF');
   WHEN INVALID_MOLECULE_ID THEN
      RAISE_APPLICATION_ERROR(-20118, 'This is not a valid Molecule ID');
   WHEN SEC_MOL_LIST_NOT_EMPTY THEN
      RAISE_APPLICATION_ERROR(-20119, 'MDM_V_THEMES_IOF');
   WHEN INVALID_THEME_NO THEN
      RAISE_APPLICATION_ERROR(-20101, 'This is not a valid Theme No');
   WHEN DELETE_NO_MORE_POSSIBLE THEN
      RAISE_APPLICATION_ERROR(-20400, 'Theme cannot be deleted when the deletion is not on the same day, on which the Theme has been inserted');
   WHEN THEME_NO_ONLY_INSERT THEN
      RAISE_APPLICATION_ERROR(-20400, 'Theme No cannot be updated');
   WHEN DESCRIPTION_TOO_LONG THEN
      RAISE_APPLICATION_ERROR(-20400, 'The automatically generated Theme Description "'
                                      || V_DESCRIPTION
                                      || '" is too long');
   WHEN THEME_DESC_PROPOSAL_TOO_LONG THEN
      RAISE_APPLICATION_ERROR(-20400, 'The automatically generated Short Description Proposal "'
                                      || :OLD.THEME_DESC_PROPOSAL
                                      || '" is too long');
   WHEN THEME_DESC_ALT_TOO_LONG THEN
      RAISE_APPLICATION_ERROR(-20400, 'The automatically generated Downstream Theme Description "'
                                      || :OLD.THEME_DESC_ALT
                                      || '" is too long');
   WHEN THEME_NO_CANNOT_BE_INSERTED THEN
      RAISE_APPLICATION_ERROR(-20400, 'This Theme No already exists');
   WHEN ONLYONEOFFICIALCHANGEPERDAY THEN
      RAISE_APPLICATION_ERROR(-20400, 'Official Change for this Theme No and Day already exists');
   WHEN INSERTSMUSTBEOFFICIAL THEN
      RAISE_APPLICATION_ERROR(-20400, 'New Themes can only be inserted by Official Changes');
   WHEN THEMEDESCRIPTIONMANDATORY THEN
      RAISE_APPLICATION_ERROR(-20400, 'If Pharma Rx Portfolio Project is set to "No", then the Theme Description must be filled');
   WHEN THEME_DESC_NOT_UNIQUE THEN
      RAISE_APPLICATION_ERROR(-20400, 'This Theme Description already exists');
   WHEN PORTF_PROJ_MOL_CRE_ERR THEN
      RAISE_APPLICATION_ERROR(-20120, 'MDM_V_THEMES_IOF');
   WHEN DEBUGGING THEN
      RAISE_APPLICATION_ERROR(-20900, 'Debug in Themes IOF standard');
END;