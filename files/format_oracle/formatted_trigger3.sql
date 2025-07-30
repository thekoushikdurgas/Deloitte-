DECLARE v_trigger_name VARCHAR2 (100) := 'COMPANY_ADDRESSES_IOF';

cntr PLS_INTEGER;

err_upd
EXCEPTION;

err_ins
EXCEPTION;

err_ctry_chg
EXCEPTION;

err_not_allowed_to_invalidate
EXCEPTION;

v_userid VARCHAR2 (100);

test_err
EXCEPTION;

v_country_cd core.countries.country_cd%TYPE;

v_company_type_cd cfg.cfg_companies.company_type_cd%TYPE;

err_ins_legal_addr
EXCEPTION;

v_valid_from cfg.cfg_company_addresses.valid_from%TYPE;

BEGIN BEGIN v_userid := txo_util.get_userid;


EXCEPTION WHEN others THEN v_userid := USER;

END;

cntr := 0;


SELECT COUNT (*) INTO cntr
FROM cfg_v_company_addresses
WHERE company_cd = nvl(:new.company_cd, :old.company_cd)
    AND address_type_cd = nvl(:new.address_type_cd, :old.address_type_cd);

IF (inserting) THEN IF (cntr > 0) THEN RAISE err_ins;

END IF;

END IF;

IF (inserting
    OR updating) THEN
SELECT company_type_cd INTO v_company_type_cd
FROM cfg_v_companies
WHERE company_cd = NVL (:new.company_cd,
                             :old.company_cd);

IF (v_company_type_cd NOT IN ('L',
                              'A')
    AND nvl(:new.address_type_cd, :old.address_type_cd) IN ('L')) THEN RAISE err_ins_legal_addr;

END IF;

IF (nvl(:new.address_type_cd, :old.address_type_cd) IN ('P',
                                                        'L')) THEN IF (nvl(:old.valid_from, trunc(sysdate)) = nvl(:new.valid_from, trunc(sysdate))
                                                                       AND :old.country_id <> :new.country_id) THEN RAISE err_ctry_chg;

END IF;

IF (cntr = 0) THEN mdm_util_addresses.modify_company_address(p_company_cd => :new.company_cd , p_address_type_cd => :new.address_type_cd , p_additional_name => :new.additional_name , p_street => :new.street , p_house_no => :new.house_no , p_building => :new.building , p_additional_info => :new.additional_info , p_zip_code => :new.zip_code , p_city=> :new.city , p_district_name => :new.district_name , p_country_id => :new.country_id , p_latitude => :new.latitude , p_longitude => :new.longitude , p_address_remark => :new.address_remark , p_valid_from => :new.valid_from , p_action_type => 'INSERT');

ELSE IF (nvl(:old.valid_from, trunc(sysdate)) <> nvl(:new.valid_from, trunc(sysdate))
         AND :old.country_id <> :new.country_id) THEN mdm_util_addresses.modify_company_address(p_company_cd => :new.company_cd , p_address_type_cd => :new.address_type_cd , p_additional_name => :new.additional_name , p_street => :new.street , p_house_no => :new.house_no , p_building => :new.building , p_additional_info => :new.additional_info , p_zip_code => :new.zip_code , p_city=> :new.city , p_district_name => :new.district_name , p_country_id => :new.country_id , p_latitude => :new.latitude , p_longitude => :new.longitude , p_address_remark => :new.address_remark , p_valid_from => :new.valid_from , p_action_type => 'CTRY_CHANGE');

cntr := 0;


SELECT count(*) INTO cntr
FROM cfg_v_companies
WHERE company_cd = :new.company_cd
    AND valid_ind = 'Y'
    AND cbc_gbe_scope = 'Y'
    AND company_type_cd IN ('B',
                            'L');

IF (:new.address_type_cd = 'P'
    AND cntr > 0) THEN
SELECT country_cd INTO v_country_cd
FROM mdm_v_countries
WHERE country_id = :new.country_id;

IF (to_char(:new.valid_from, 'dd.mm') = '01.01') THEN v_valid_from := to_date(add_months(trunc(:new.valid_from, 'yyyy'), 10), 'dd.mm.yyyy');

ELSE v_valid_from := to_date(add_months(trunc(:new.valid_from, 'yyyy'), 22), 'dd.mm.yyyy');

END IF;

mdm_util_companies.modifycompanymapping_ce_ju (i_company_cd => :new.company_cd, i_reporting_entity_cd => 'J-' || v_country_cd, i_valid_from_date => v_valid_from, i_valid_to_date => NULL, i_change_user => v_userid, i_mapping_type => 'JU', i_action_type => 'INSERT');

IF (v_company_type_cd = 'L') THEN
FOR v_rec IN
    (SELECT company_cd
     FROM cfg_v_companies
     WHERE legal_company_cd = :new.company_cd
         AND valid_ind = 'Y'
         AND cbc_gbe_scope = 'Y'
         AND company_type_cd IN ('O',
                                 'V')) LOOP mdm_util_companies.modifycompanymapping_ce_ju (i_company_cd => v_rec.company_cd, i_reporting_entity_cd => 'J-' || v_country_cd, i_valid_from_date => v_valid_from, i_valid_to_date => NULL, i_change_user => v_userid, i_mapping_type => 'JU', i_action_type => 'INSERT');

END LOOP;

END IF;

END IF;

ELSE mdm_util_addresses.modify_company_address(p_company_cd => :new.company_cd , p_address_type_cd => :new.address_type_cd , p_additional_name => :new.additional_name , p_street => :new.street , p_house_no => :new.house_no , p_building => :new.building , p_additional_info => :new.additional_info , p_zip_code => :new.zip_code , p_city=> :new.city , p_district_name => :new.district_name , p_country_id => :new.country_id , p_latitude => :new.latitude , p_longitude => :new.longitude , p_address_remark => :new.address_remark , p_valid_from => :new.valid_from , p_action_type => 'UPDATE');

END IF;

END IF;

END IF;

IF (nvl(:new.address_type_cd, :old.address_type_cd) NOT IN ('P',
                                                            'L')) THEN IF (cntr = 0) THEN mdm_util_addresses.modify_company_address(p_company_cd => :new.company_cd , p_address_type_cd => :new.address_type_cd , p_additional_name => :new.additional_name , p_street => :new.street , p_house_no => :new.house_no , p_building => :new.building , p_additional_info => :new.additional_info , p_zip_code => :new.zip_code , p_city=> :new.city , p_district_name => :new.district_name , p_country_id => :new.country_id , p_latitude => :new.latitude , p_longitude => :new.longitude , p_address_remark => :new.address_remark , p_valid_from => :new.valid_from , p_action_type => 'INSERT');

ELSE mdm_util_addresses.modify_company_address(p_company_cd => :new.company_cd , p_address_type_cd => :new.address_type_cd , p_additional_name => :new.additional_name , p_street => :new.street , p_house_no => :new.house_no , p_building => :new.building , p_additional_info => :new.additional_info , p_zip_code => :new.zip_code , p_city=> :new.city , p_district_name => :new.district_name , p_country_id => :new.country_id , p_latitude => :new.latitude , p_longitude => :new.longitude , p_address_remark => :new.address_remark , p_valid_from => :new.valid_from , p_action_type => 'UPDATE');

END IF;

END IF;

END IF;

IF (deleting) THEN IF (nvl(:new.address_type_cd, :old.address_type_cd) IN ('L',
                                                                           'P')) THEN RAISE err_not_allowed_to_invalidate;

END IF;

mdm_util_addresses.modify_company_address(p_company_cd => nvl(:new.company_cd, :old.company_cd) , p_address_type_cd => nvl(:new.address_type_cd, :old.address_type_cd) , p_action_type => 'DELETE');

END IF;


EXCEPTION WHEN err_upd THEN raise_application_error (-20111, 'The address cannot be updated because the Address type is different. Old address type: '||:old.address_type_cd||' New address type: '||:new.address_type_cd);

WHEN err_ins THEN raise_application_error (-20112, 'An address already exists for this Company and Address type. To modify the existing address, please use the Update button.');

WHEN err_ctry_chg THEN raise_application_error (-20113, 'The company country modified but not the Valid From Date. Please update also the Valid From Date.');

WHEN test_err THEN raise_application_error (-20113, 'New: '||:new.company_cd||' Old:'||:old.company_cd||'Count: '||cntr);

WHEN err_ins_legal_addr THEN raise_application_error (-20113, 'The legal address cannot be inserted for this type of company');

WHEN err_not_allowed_to_invalidate THEN raise_application_error (-20113, 'It is not allowed to invalidate/delete this type of address');

END;