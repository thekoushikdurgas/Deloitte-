declare
   invalid_theme_no exception;
   delete_no_more_possible exception;
   theme_no_only_insert exception;
   description_too_long exception;
   theme_desc_proposal_too_long exception;
   theme_desc_alt_too_long exception;
   theme_no_cannot_be_inserted exception;
   onlyoneofficialchangeperday exception;
   insertsmustbeofficial exception;
   themedescriptionmandatory exception;
   theme_desc_not_unique exception;
   in_prep_not_portf_proj exception;
   in_prep_not_closed exception;
   invalid_molecule_id exception;
   sec_mol_list_not_empty exception;
   admin_update_only exception;
   portf_proj_mol_cre_err exception;
   debugging exception;
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
   v_molecule_id varchar2(5) := null;
   v_molecule_rg_no varchar2(20) := null;
   v_molec_in_lic_prtnr varchar2(15) := null;
   v_new_rg_no v_theme_molecules.rg_no%type;
   v_comparator_ind v_theme_molecules.comparator_ind%type;
   v_theme_desc_proposal mdm_v_themes_mtn.theme_desc_proposal%type;
   v_short_name  varchar2(30);
   c_molecule_type_id constant v_molecule_types.molecule_type_id%type := 99; -- Other Program
   c_pharmacological_type_id constant v_pharmacological_types.pharmacological_type_id%type := 19; -- Unknown
   v_evolved_nmp_cnt          PLS_INTEGER;
   v_trademark_no             v_themes.trademark_no%type;
   v_molecule_type_id         v_molecule_types.molecule_type_id%type;
   v_pharmacological_type_id  v_pharmacological_types.pharmacological_type_id%type;
begin
   -- check user
   select nvl(txo_security.get_userid, user) into v_userid from dual;

   -- v_is_admin_cnt = 0 => is NOT a full admin user (MDMS_THEME_ADMIN_FULL_ACCESS)
   -- v_is_admin_cnt > 0 => is a full admin user (MDMS_THEME_ADMIN_FULL_ACCESS)
   select count(*)
   into v_is_admin_cnt
   from txo_users_roles_map
   where role_id in (315)
   and userid = v_userid;

   -- find next free rg_no which may be used later in this trigger :
   select new_rg_no
   into v_new_rg_no
   from (select new_rg_no
         from (select rownum as new_rg_no
               from dual
               connect by 1 = 1
               and rownum <= 6999)
         where new_rg_no > 5999
         minus
         select to_number(rg_no) from v_theme_molecules)
   where rownum = 1;

   if (:new.in_prep_ind = 'Y')
   then
      if (:new.portf_proj_cd <> 'Y')
      then
         raise in_prep_not_portf_proj;
      end if;

      if (:new.status_desc <> 'CLOSED'
          and v_is_admin_cnt = 0) -- not a full admin user, i.e. member of portfolio team (only)
      then
         raise in_prep_not_closed;
      end if;

      if (:new.molecule_id is null)
      then
         txo_util.set_warning('No Molecule assigned to In-Prep Theme ' || :new.theme_no || '!');
      end if;
   end if;

   -- set THEME_MOLECULE RG Number for first assignment of molecule
   if (:new.molecule_id is not null)
   then
      begin
         select rg_no
               ,m.comparator_ind
         into v_molecule_rg_no
             ,v_comparator_ind
         from v_theme_molecules m
         where molecule_id = :new.molecule_id
         and m.valid_ind = 'Y';
      exception
         when no_data_found
         then
            raise invalid_molecule_id;
      end;

      if (v_molecule_rg_no is null)
      then
         if (v_comparator_ind = 'Y')
         then
            null; -- no RG_NO for Comparators -----------------------------
         else --   for Roche molecules ----------------------------------
            -- first time assignment as RG_NO is empty.
            -- set RG_NO to RG + first theme_no the molecule was ever assigned to
            update v_theme_molecules
            set rg_no = v_new_rg_no --:new.theme_no
            where molecule_id = :new.molecule_id;
         end if;
      end if;
   end if;

   -- RAISE debugging;
   -- The Parameter :NEW.RESLIN_DESC_CONCAT consists of 4 fields
   v_odg_no := substr(:new.reslin_desc_concat, 1, 2);
   v_resgrp_cd := substr(:new.reslin_desc_concat, 4, 2);
   v_reslin_cd := substr(:new.reslin_desc_concat, 7, 2);
   v_reslin_desc := substr(:new.reslin_desc_concat, 12, length(:new.reslin_desc_concat));

   if (:new.status_desc is not null)
   then
      select status_cd
      into v_status_cd
      from mdm_v_theme_status
      where state_desc = :new.status_desc;
   else
      v_status_cd := null;
   end if;

   if (:new.dba_desc_concat is not null)
   then
      select dba_cd
      into v_dba_cd
      from mdm_v_disease_biology_areas
      where dba_short_desc || ' - ' || dba_desc = :new.dba_desc_concat;
   else
      v_dba_cd := null;
   end if;

   v_molec_in_lic_prtnr := gmd_util_themes.get_molec_in_lic_prtnr(:new.molecule_id);

   if (:new.official_ind = 'N')
      then
         v_trademark_no := :new.trademark_no;
   else
      v_trademark_no := :old.trademark_no;
   END IF;

	v_theme_desc_proposal := gmd_util_themes.get_theme_short_name(p_theme_no_portf => :new.theme_no,p_molecule_id_portf => :new.molecule_id,p_prod_short_cd_portf => :new.prod_short_cd,p_odg_no_port => v_odg_no,p_resgrp_cd_port => v_resgrp_cd,p_reslin_cd_port => v_reslin_cd,p_line_ext_info_port => :new.line_ext_info,p_in_lic_prtnr_portf => null,p_trademark_no_portf => v_trademark_no,p_trunc_desc_length => 'N');

	 if (:new.manual_short_desc is null and length(v_theme_desc_proposal) > 30)
	 then
		raise theme_desc_proposal_too_long;
	 end if;

	v_short_name := coalesce(:new.manual_short_desc, v_theme_desc_proposal);

   if (inserting)
   then
      if (:new.in_prep_ind = 'N' --  only admins may update
         and v_is_admin_cnt = 0) -- current user is NOT and admin user
      then
         raise admin_update_only;
      end if;

      -- CMA 1685, automatic molecule creation
      -- CMA 1820, add RG_NO to inserted values
      v_molecule_id := :new.molecule_id;

      if (:new.portf_proj_cd = 'Y' and :new.molecule_id is null)
      then
         if (nvl(:new.manual_short_desc, :new.theme_desc_proposal) is null)
         then
            raise portf_proj_mol_cre_err;
         else
            insert into mdm_v_theme_molecules_mtn(molecule_desc
                                                 ,valid_ind
                                                 ,rg_no
                                                 ,cancer_immunotherapy_ind
                                                 ,molecule_type_id
                                                 ,pharmacological_type_id)
                values (nvl(:new.manual_short_desc, :new.theme_desc_proposal)
                       ,'Y'
                       ,v_new_rg_no
                       ,'N'
                       ,c_molecule_type_id
                       ,c_pharmacological_type_id);

            select molecule_id
            into v_molecule_id
            from v_theme_molecules
            where molecule_desc = nvl(:new.manual_short_desc, :new.theme_desc_proposal)
            and valid_ind = 'Y'
            and rg_no = v_new_rg_no
            and cancer_immunotherapy_ind = 'N'
            and molecule_type_id = c_molecule_type_id
            and pharmacological_type_id = c_pharmacological_type_id;

            --  create molecule mapping (Primary Molecule)
            insert into theme_molecule_map tmmap(tmmap.theme_no
                                                ,tmmap.molecule_id
                                                ,tmmap.molecule_seq_no
                                                ,tmmap.valid_ind)
             values (:new.theme_no, v_molecule_id, 1, 'Y'); -- primary molecule!
         end if;
      end if;

      --########################################
      --# Check if only valid values are given #
      --########################################
      -- VERIFY THEME_NO -----------------------------
      case length(:new.theme_no)
         when 4
         then
            if (substr(:new.theme_no, 1, 1) not between 0 and 9
               or substr(:new.theme_no, 2, 1) not between 0 and 9
               or substr(:new.theme_no, 3, 1) not between 0 and 9
               or substr(:new.theme_no, 4, 1) not between 0 and 9)
            then
               raise invalid_theme_no;
            end if;
         when 5
         then
            if (substr(:new.theme_no, 1, 1) not between 0 and 9
               or substr(:new.theme_no, 2, 1) not between 0 and 9
               or substr(:new.theme_no, 3, 1) not between 0 and 9
               or substr(:new.theme_no, 4, 1) not between 0 and 9
               or substr(:new.theme_no, 5, 1) not between 0 and 9)
            then
               raise invalid_theme_no;
            end if;
         else
            raise invalid_theme_no;
      end case;

      v_counter := null;

      -- Is this theme_no really new?
      select count(t.theme_no)
      into v_counter
      from (select theme_no from v_themes
            union all
            select theme_no from gmd.themes_archive) t
      where t.theme_no = :new.theme_no;

      if (v_counter > 0)
      then
         raise theme_no_cannot_be_inserted;
      end if;

      v_counter := null;

      v_d_registrat_date := sysdate;

      -- VERIFY OFFICIAL-IND --------------------------
      if (:new.official_ind = 'N')
      then
         raise insertsmustbeofficial;
      end if;

      if (upper(:new.portf_proj_cd) = 'N')
      then
         if (:new.theme_desc is null -- when description is not generated,
            or length(:new.theme_desc) = 0) -- then it is mandatory
         then
            raise themedescriptionmandatory;
         end if;
      end if;

      -- The Theme Description is generated automatically
      if (upper(:new.portf_proj_cd) = 'Y') -- theme desc is updated automatically only for portfolio projects
      /* -- even for initially closed themes the generated description is inserted
         -- but closed themes will not be updated (unless they are IN_PREP themes)
       AND (v_status_cd <> 'C' -- usually only "not closed" themes are updated
                              OR :new.in_prep_ind = 'Y') -- all stati allowed for in preparation themes
                              */
      then
         v_description := gmd.gmd_util_themes.get_theme_desc_portfolio(p_theme_no_portf => null
                                                                      ,p_molecule_id_portf => v_molecule_id
                                                                      ,p_prod_short_cd_portf => :new.prod_short_cd
                                                                      ,p_odg_no_port => v_odg_no
                                                                      ,p_resgrp_cd_port => v_resgrp_cd
                                                                      ,p_reslin_cd_port => v_reslin_cd
                                                                      ,p_line_ext_info_port => :new.line_ext_info
                                                                      ,p_in_lic_prtnr_portf => v_molec_in_lic_prtnr
                                                                      ,p_trademark_no_portf => :new.trademark_no
                                                                      ,p_short_name_portf => :new.short_name
                                                                      ,p_trunc_desc_length => 'N');

         if (length(v_description) > 90)
         then
            raise description_too_long;
         end if;

         v_description := trim(v_description);
         v_portf_proj_cd := 'Y';
      else
         -- The given Theme Description is inserted
         v_description := :new.theme_desc;
         v_portf_proj_cd := 'N';
      end if; -- :NEW.PORTF_PROJ_CD = 'Y'

      -- NOW VERIFY UNIQUENESS OF THEME_DESC --------------
      v_counter := null;

      select count(t.theme_no)
      into v_counter
      from v_themes t
      where t.theme_desc = v_description;

      if (v_counter > 0)
      then
         raise theme_desc_not_unique;
      end if;

      v_counter := null;
      v_valid_to := to_date('09.09.9999', 'DD.MM.YYYY');

	  v_short_name := nvl(:new.manual_short_desc, substr(v_description, 1, 30));

      insert into gmd.themes(theme_no
                            ,registrat_date
                            ,odg_no
                            ,resgrp_cd
                            ,reslin_cd
                            ,theme_desc
                            ,short_name
                            ,status_cd
                            ,dba_cd
                            ,in_prep_ind
                            ,prod_short_cd
                            ,trademark_no
                            ,bio_activity
                            ,applicant
                            ,contact
                            ,registrar
                            ,line_ext_info
                            ,portf_proj_cd
                            ,co_dev_prtnr
                            ,technology_prtnr
                            ,official_ind
                            ,co_mar_prtnr
                            ,valid_to
                            ,portf_da_group_id
                            ,manual_short_desc)
       values (:new.theme_no
              ,v_d_registrat_date
              ,v_odg_no
              ,v_resgrp_cd
              ,v_reslin_cd
              ,v_description
              ,v_short_name
              ,v_status_cd
              ,v_dba_cd
              ,:new.in_prep_ind
              ,:new.prod_short_cd
              ,:new.trademark_no
              ,:new.bio_activity
              ,:new.applicant
              ,:new.contact
              ,txo_util.get_userid
              ,:new.line_ext_info
              ,v_portf_proj_cd
              ,:new.co_dev_prtnr
              ,:new.technology_prtnr
              ,:new.official_ind
              ,:new.co_mar_prtnr
              ,v_valid_to
              ,:new.portf_da_group_id
              ,:new.manual_short_desc);


      if (:old.molecule_id is null and :new.molecule_id is not null)
      then
         -- handle primary molecule mapping to this theme
         insert into mdm_v_theme_molecule_map_mtn a(a.theme_no
                                                   ,a.molecule_id
                                                   ,a.molecule_seq_no
                                                   ,a.valid_ind)
          values (:new.theme_no, v_molecule_id, 1, 'Y'); --(PRIMARY, molecule_seq_no = 1)
      end if;


   -- End Code  for Inserting
   elsif (updating)
   then
      -- check admin access (role 315)
      if (:old.in_prep_ind = 'N'
          or(:old.in_prep_ind = 'Y'
             and:new.in_prep_ind = 'N')) --  only admins may update
         and v_is_admin_cnt = 0 -- current user is NOT and admin user
      then
         raise admin_update_only;
      end if;

      if (:new.theme_no <> :old.theme_no)
      then
         raise theme_no_only_insert;
      end if;

      -- CMA 1544 Registrat_date is
      --   * always sysdate for official updates
      --   * always :OLD.registrat_date for inofficial updates

      if (:new.official_ind = 'N')
      then
         -- inofficial => do not change registrat_date
         v_d_registrat_date := to_date(:old.registrat_date, 'dd-mm-yyyy');
      else -- it is an official change
         -- official change => registrat_date will be set to sysdate
         v_d_registrat_date := sysdate;
      end if;

      if (upper(:new.portf_proj_cd) = 'Y' -- theme desc is updated automatically only for portfolio projects
         and(v_status_cd <> 'C' -- usually only "not closed" themes are updated
             or:new.in_prep_ind = 'Y')) -- all stati allowed for in preparation themes
      then
         v_description := gmd.gmd_util_themes.get_theme_desc_portfolio(p_theme_no_portf => :new.theme_no
                                                                      ,p_molecule_id_portf => :new.molecule_id
                                                                      ,p_prod_short_cd_portf => :new.prod_short_cd
                                                                      ,p_odg_no_port => v_odg_no
                                                                      ,p_resgrp_cd_port => v_resgrp_cd
                                                                      ,p_reslin_cd_port => v_reslin_cd
                                                                      ,p_line_ext_info_port => :new.line_ext_info
                                                                      ,p_in_lic_prtnr_portf => v_molec_in_lic_prtnr
                                                                      ,p_trademark_no_portf => :new.trademark_no
                                                                      ,p_short_name_portf => :new.short_name
                                                                      ,p_trunc_desc_length => 'N');

         v_description := trim(v_description);
         v_portf_proj_cd := 'Y';
      else
         if (:new.theme_desc is null -- when description is not generated,
            or length(:new.theme_desc) = 0) -- then it is mandatory
         then
            raise themedescriptionmandatory;
         else
            v_description := :new.theme_desc;

            v_portf_proj_cd := :new.portf_proj_cd;
         end if;
      end if;

      if (length(v_description) > 90)
      then
         raise description_too_long;
      end if;

      -- NOW VERIFY UNIQUENESS OF THEME_DESC --------------
      --(but not within the same theme_no, then is no uniqueness required)
      v_counter := null;

      select count(t.theme_no)
      into v_counter
      from v_themes t
      where t.theme_desc = v_description
      and t.theme_no <> :new.theme_no;

      if (v_counter > 0)
      then
         raise theme_desc_not_unique;
      end if;

      v_counter := null;

      --  Code for INOFFICIAL Changes
      if (:new.official_ind = 'N')
      then

         update gmd.themes
         set odg_no = v_odg_no
            ,resgrp_cd = v_resgrp_cd
            ,reslin_cd = v_reslin_cd
            ,theme_desc = v_description
            ,short_name = v_short_name
            ,status_cd = v_status_cd
            ,dba_cd = v_dba_cd
            ,in_prep_ind = :new.in_prep_ind
            ,prod_short_cd = :new.prod_short_cd
            ,trademark_no = :new.trademark_no
            ,bio_activity = :new.bio_activity
            ,applicant = :new.applicant
            ,contact = :new.contact
            ,line_ext_info = :new.line_ext_info
            ,portf_proj_cd = v_portf_proj_cd
            ,co_dev_prtnr = :new.co_dev_prtnr
            ,technology_prtnr = :new.technology_prtnr
            ,official_ind = :new.official_ind
            ,co_mar_prtnr = :new.co_mar_prtnr
            ,portf_da_group_id = :new.portf_da_group_id
            ,manual_short_desc = :new.manual_short_desc
         -- registrat_date is not changed
         where theme_no = :new.theme_no
         and to_date(registrat_date, 'DD-MM-YYYY') = v_d_registrat_date;
      else
         -- Code for OFFICIAL changes  :NEW.OFFICIAL_IND = 'Y'
         -- then this is  the first and only record for this registrat-date
         v_counter := null;

         -- only one official change allowed per day
         select count(*)
         into v_counter
         from v_themes t
         where trunc(t.registrat_date) = trunc(sysdate)
         and t.theme_no = :new.theme_no;

         if (v_counter > 0)
         then
            raise onlyoneofficialchangeperday;
         end if;

         v_counter := null;

         update gmd.themes
         set odg_no = v_odg_no
            ,resgrp_cd = v_resgrp_cd
            ,reslin_cd = v_reslin_cd
            ,theme_desc = v_description
            ,short_name = v_short_name
            ,status_cd = v_status_cd
            ,dba_cd = v_dba_cd
            ,in_prep_ind = :new.in_prep_ind
            ,prod_short_cd = :new.prod_short_cd
            ,trademark_no = :new.trademark_no
            ,bio_activity = :new.bio_activity
            ,applicant = :new.applicant
            ,contact = :new.contact
            ,line_ext_info = :new.line_ext_info
            ,portf_proj_cd = v_portf_proj_cd
            ,co_dev_prtnr = :new.co_dev_prtnr
            ,technology_prtnr = :new.technology_prtnr
            ,official_ind = :new.official_ind
            ,co_mar_prtnr = :new.co_mar_prtnr
            ,registrat_date = sysdate
            ,registrar = v_userid
            ,portf_da_group_id = :new.portf_da_group_id
            ,manual_short_desc = :new.manual_short_desc
         where theme_no = :new.theme_no;
      end if;

      -- handle primary molecule mapping to this theme
      -- this code is identical for official and in-official changes
      case
         when :old.molecule_id is null and :new.molecule_id is not null
         then
            -- insert a new mapping (PRIMARY, molecule_seq_no = 1)
            insert into mdm_v_theme_molecule_map_mtn a(a.theme_no
                                                      ,a.molecule_id
                                                      ,a.molecule_seq_no
                                                      ,a.valid_ind)
             values (:new.theme_no, :new.molecule_id, 1, 'Y');
         when :old.molecule_id is not null and :new.molecule_id is not null
         then
            -- update an existing mapping (PRIMARY, molecule_seq_no = 1)
            update mdm_v_theme_molecule_map a
            set a.molecule_id = :new.molecule_id, a.valid_ind = 'Y'
            where a.theme_no = :new.theme_no
            and a.molecule_seq_no = 1
            and a.valid_ind = 'Y';
         when :old.molecule_id is not null and :new.molecule_id is null
         then
            select count(*)
            into v_sec_mol_cnt
            from mdm_v_theme_molecule_map_mtn a
            where a.theme_no = :new.theme_no
            and a.molecule_seq_no > 1
            and a.valid_ind = 'Y';

            if (v_sec_mol_cnt > 0) -- a valid secondary molecule exists
            then
               raise sec_mol_list_not_empty; -- error
            else
               -- soft-delete an existing mapping (PRIMARY, molecule_seq_no = 1)
               update mdm_v_theme_molecule_map a
               set a.valid_ind = 'N'
               where a.molecule_id = :old.molecule_id
               and a.theme_no = :new.theme_no
               and a.molecule_seq_no = 1
               and a.valid_ind = 'Y';
            end if;
         else
            null;
      end case;


   elsif (deleting)
   then
      if ((:old.in_prep_ind = 'N') --  only admins may delete
         and v_is_admin_cnt = 0) -- current user is NOT and admin user
      then
         raise admin_update_only;
      end if;

      -- deleting is only possible, if theme_no has been
      -- inserted on the same day
      -- only if this change has been
      if (trunc(to_date(:old.registrat_date, 'DD-MM-YYYY')) = trunc(sysdate))
      then
         delete from gmd.themes a
         where a.theme_no = :old.theme_no
         and trunc(a.registrat_date) = trunc(sysdate);
      else
         raise delete_no_more_possible;
      end if;
   end if;

   --  Code for Inserting, Updating, Deleting

	IF (INSERTING OR UPDATING)
    THEN

		If (:new.proposal_id is not null and :old.proposal_id is null)
			  then
			      -- check if the entered NMP is evolved
				  SELECT count(*) INTO v_evolved_nmp_cnt
				  FROM mdm_v_new_medicine_proposals_mtn
				  WHERE proposal_id = :new.proposal_id
				  AND proposal_status_cd = 'E' ;
				   ----------
				  -- if the proposal id is set and the NMP is not evolved then update the corresponding
				  -- New Medicinie Proposal status to evolved
				if (v_evolved_nmp_cnt = 0) then
					 update mdm_v_new_medicine_proposals_mtn
					 set proposal_status_cd = 'E', evolved_theme_no = :new.theme_no,
						 proposal_name = v_short_name,
						 reason_for_change = '** Automatic update of proposal_name after short_name change in evolved theme **'
					 where proposal_id = :new.proposal_id;
				end if;


			  else
				 if (:new.proposal_id is null and :old.proposal_id is not null)
				 then
					update mdm_v_new_medicine_proposals_mtn
					set proposal_status_cd = 'A', evolved_theme_no = null
					where proposal_id = :old.proposal_id;
				 else
					if (:new.proposal_id is not null and :old.proposal_id is not null and :new.proposal_id <> :old.proposal_id)
					then

					   -- set to Active the old New Medicine Proposal
					   update mdm_v_new_medicine_proposals_mtn
					   set proposal_status_cd = 'A', evolved_theme_no = null
					   where proposal_id = :old.proposal_id;

					   -- set to Evolved the new choosen New Medicine Proposal
					   update mdm_v_new_medicine_proposals_mtn
					   set proposal_status_cd = 'E', evolved_theme_no = :new.theme_no,
						   proposal_name = v_short_name,
						   reason_for_change = '** Automatic update of proposal_name after short_name change in evolved theme **'
					   where proposal_id = :new.proposal_id;
					end if;
				 end if;
		end if;

		-- short_name update
        IF (NVL(:new.proposal_id, 0) = NVL(:old.proposal_id, 0) and NVL(:old.short_name,'-') <> NVL(v_short_name,'-'))
        THEN

		  -- check if this is an evolved proposal
          SELECT count(*) INTO v_evolved_nmp_cnt
          FROM mdm_v_new_medicine_proposals_mtn nmp
          WHERE nmp.evolved_theme_no =:new.theme_no
            AND nmp.proposal_status_cd = 'E' ;


          IF (v_evolved_nmp_cnt > 0)
          THEN

		    -- short_name has changed so proposal_name must be updated accordingly
            UPDATE mdm_v_new_medicine_proposals_mtn nmp
            SET nmp.proposal_name = v_short_name,
                nmp.reason_for_change = '** Automatic update of proposal_name after short_name change in evolved theme **'
            WHERE nmp.evolved_theme_no =:new.theme_no
            AND nmp.proposal_status_cd = 'E' ;
          END IF;
        END IF;
    END IF;

	-- handle New Medicine Proposals with theme_no starting with 71.. or 74
	IF (INSERTING and :new.theme_no is not null and gmd_util_themes.get_themes_range_automatic_nmp(:new.theme_no) = 'Y')
    THEN
	    IF (:new.proposal_id is not null)
		THEN
			  SELECT count(*) INTO v_evolved_nmp_cnt
			  FROM mdm_v_new_medicine_proposals_mtn
			  WHERE proposal_id = :new.proposal_id
			  AND proposal_name = v_short_name
			  AND proposal_status_cd = 'E' ;
		END IF;

		-- automatic create NMP only if no prposal_id is selected or the selected one is evolved
		IF (:new.proposal_id is null or (:new.proposal_id is not null and v_evolved_nmp_cnt = 0))
		THEN
		   IF (:new.molecule_id is not null)
		   THEN
			  begin
				 select
						pharmacological_type_id
					   ,molecule_type_id
				 into   v_pharmacological_type_id
					   ,v_molecule_type_id
				 from v_theme_molecules m
				 where molecule_id = :new.molecule_id
				 and m.valid_ind = 'Y';
			  exception
				 when no_data_found
				 then
					raise invalid_molecule_id;
			  end;
			END IF;

			INSERT INTO mdm_v_new_medicine_proposals_mtn
						(proposal_status_cd,
						 evolved_theme_no,
						 proposal_name,
						 pharmacological_type_id,
						 molecule_type_id,
						 reason_for_change)
			VALUES     ('E',
						:new.theme_no,
						v_short_name,
						NVL(v_pharmacological_type_id, c_pharmacological_type_id),
						NVL(v_molecule_type_id, c_molecule_type_id),
						'** Automatic creation of nmp for early development themes **');
		END IF;
	END IF;

   begin
      -- set variable
      -- is_from_theme_validity_check := TRUE;
      for i1 in (select a.theme_no
                       ,a.registrat_date
                 from v_themes a
                 where a.valid_to <= trunc(sysdate))
      loop
         delete from gmd.themes
         where theme_no = i1.theme_no
         and registrat_date = i1.registrat_date;
      end loop;
   end;

exception
   when admin_update_only
   then
      raise_application_error(-20115, 'MDM_V_THEMES_IOF');
   when in_prep_not_portf_proj
   then
      raise_application_error(-20116, 'MDM_V_THEMES_IOF');
   when in_prep_not_closed
   then
      raise_application_error(-20117, 'MDM_V_THEMES_IOF');
   when invalid_molecule_id
   then
      raise_application_error(-20118, 'This is not a valid Molecule ID');
   when sec_mol_list_not_empty
   then
      raise_application_error(-20119, 'MDM_V_THEMES_IOF');
   when invalid_theme_no
   then
      raise_application_error(-20101, 'This is not a valid Theme No');
   when delete_no_more_possible
   then
      raise_application_error(
         -20400
        ,'Theme cannot be deleted when the deletion is not on the same day, on which the Theme has been inserted');
   when theme_no_only_insert
   then
      raise_application_error(-20400, 'Theme No cannot be updated');
   when description_too_long
   then
      raise_application_error(-20400
                             ,'The automatically generated Theme Description "' || v_description || '" is too long');
   when theme_desc_proposal_too_long
   then
      raise_application_error(
         -20400
        ,'The automatically generated Short Description Proposal "' || :old.theme_desc_proposal || '" is too long');
   when theme_desc_alt_too_long
   then
      raise_application_error(
         -20400
        ,'The automatically generated Downstream Theme Description "' || :old.theme_desc_alt || '" is too long');
   when theme_no_cannot_be_inserted
   then
      raise_application_error(-20400, 'This Theme No already exists');
   when onlyoneofficialchangeperday
   then
      raise_application_error(-20400, 'Official Change for this Theme No and Day already exists');
   when insertsmustbeofficial
   then
      raise_application_error(-20400, 'New Themes can only be inserted by Official Changes');
   when themedescriptionmandatory
   then
      raise_application_error(
         -20400
        ,'If Pharma Rx Portfolio Project is set to "No", then the Theme Description must be filled');
   when theme_desc_not_unique
   then
      raise_application_error(-20400, 'This Theme Description already exists');
   when portf_proj_mol_cre_err
   then
      raise_application_error(-20120, 'MDM_V_THEMES_IOF');
   when debugging
   then
      raise_application_error(-20900, 'Debug in Themes IOF standard');
end;
