DECLARE
    v_trigger_name   VARCHAR2 (100) := 'COMPANY_ADDRESSES_IOF';
    cntr             PLS_INTEGER;
    err_upd          EXCEPTION;
    err_ins          EXCEPTION;
    err_ctry_chg     EXCEPTION;
    err_not_allowed_to_invalidate  EXCEPTION;
    v_userid                  VARCHAR2 (100);
    test_err     exception;
    v_country_cd    core.countries.country_cd%type;
    v_company_type_cd CFG.CFG_COMPANIES.COMPANY_TYPE_CD%type;
    err_ins_legal_addr EXCEPTION;
    v_valid_from    CFG.CFG_COMPANY_ADDRESSES.VALID_FROM%type;
BEGIN


BEGIN
        v_userid := txo_util.get_userid;
    EXCEPTION
        WHEN OTHERS
        THEN
            v_userid := USER;
    END;


        cntr := 0;


        SELECT COUNT (*)
          INTO cntr
          FROM cfg_v_company_addresses
         WHERE company_cd = nvl(:new.company_cd, :old.company_cd)
         and   address_type_cd = nvl(:new.address_type_cd, :old.address_type_cd);




    IF (INSERTING)
    THEN
        IF (cntr > 0)
        THEN
            RAISE err_ins;
        END IF;
    END IF;
   
IF (INSERTING or UPDATING)
THEN
   


    SELECT company_type_cd
      INTO v_company_type_cd
      FROM cfg_v_companies
     WHERE company_cd = NVL ( :new.company_cd, :old.company_cd);


    IF (v_company_type_cd not in ('L','A') and nvl(:new.address_type_cd, :old.address_type_cd) IN ('L'))
        THEN
            RAISE err_ins_legal_addr;
    END IF;






    IF (nvl(:new.address_type_cd, :old.address_type_cd) in ( 'P','L'))
     THEN
     
        IF (nvl(:old.valid_from, trunc(sysdate)) = nvl(:new.valid_from, trunc(sysdate)) AND :old.country_id <>   :new.country_id)
            THEN
                RAISE err_ctry_chg;
            END IF;
   
        IF (cntr = 0) THEN
       
        --insert address P/L + RES/INC with valid_from date
        MDM_UTIL_ADDRESSES.modify_company_address(p_company_cd          => :new.company_cd
                                                   ,p_address_type_cd   => :new.address_type_cd
                                                   ,p_additional_name   => :new.additional_name
                                                   ,p_street => :new.street
                                                   ,p_house_no => :new.house_no
                                                   ,p_building  => :new.building
                                                   ,p_additional_info => :new.additional_info
                                                   ,p_zip_code => :new.zip_code
                                                   ,p_city=> :new.city
                                                   ,p_district_name => :new.district_name
                                                   ,p_country_id => :new.country_id
                                                   ,p_latitude => :new.latitude
                                                   ,p_longitude => :new.longitude
                                                   ,p_address_remark => :new.address_remark
                                                   ,p_valid_from => :new.valid_from
                                                   ,p_action_type => 'INSERT');
       


                    ELSE
                   
                        --check if there are changes on the valid_from date and country => if YES, old records will be expired and new ones will be inserted    
                        IF (nvl(:old.valid_from, trunc(sysdate)) <> nvl(:new.valid_from, trunc(sysdate)) and :old.country_id <> :new.country_id)
                            THEN
                                    --update the P/L existing address with new valid_from -1
                                    --update the RES/INC address with valid_to = last day of the year of valid from date
                                    --insert new P/L address with new valid_from
                                    --insert new RES/INC address with first day of next year of valid from date
                                MDM_UTIL_ADDRESSES.modify_company_address(p_company_cd => :new.company_cd
                                                                       ,p_address_type_cd  => :new.address_type_cd
                                                                       ,p_additional_name => :new.additional_name
                                                                       ,p_street => :new.street
                                                                       ,p_house_no => :new.house_no
                                                                       ,p_building  => :new.building
                                                                       ,p_additional_info => :new.additional_info
                                                                       ,p_zip_code => :new.zip_code
                                                                       ,p_city=> :new.city
                                                                       ,p_district_name => :new.district_name
                                                                       ,p_country_id => :new.country_id
                                                                       ,p_latitude => :new.latitude
                                                                       ,p_longitude => :new.longitude
                                                                       ,p_address_remark => :new.address_remark
                                                                       ,p_valid_from => :new.valid_from
                                                                       ,p_action_type => 'CTRY_CHANGE');
                                --particular case for Physical address - change the JU mapping for the company    
                               
                                cntr := 0;
                               
                                --looking for B/L company types which are active and have CBC scope on Yes
                                select count(*) into cntr from cfg_v_companies where company_cd = :new.company_cd and valid_ind = 'Y' and cbc_gbe_scope = 'Y' and company_type_cd in ('B','L');
                               
                               
                                 IF (:new.address_type_cd = 'P' and cntr > 0)
                                 THEN  
                                    --update existing JU-mapping with last day of the year of valid from date
                                    --insert new JU mapping with first day of the next year of the valid from date
                                    SELECT country_cd
                                      INTO v_country_cd
                                      FROM mdm_v_countries
                                     WHERE country_id = :new.country_id;
                                   
                                    --check if the the day used is first day of the year
                                    IF (to_char(:new.valid_from, 'dd.mm') = '01.01')
                                        THEN
                                        --find the first day of the current year of valid from
                                        v_valid_from := to_date(ADD_MONTHS(trunc(:new.valid_from,'yyyy'),10),'dd.mm.yyyy');
                                    ELSE
                                        --find the first day of the next year of valid from
                                        v_valid_from := to_date(ADD_MONTHS(trunc(:new.valid_from,'yyyy'),22),'dd.mm.yyyy');


                                    END IF;
                                   
                                    mdm_util_companies.modifycompanymapping_ce_ju (
                                                i_company_cd            => :new.company_cd,
                                                i_reporting_entity_cd   => 'J-' || v_country_cd,
                                                i_valid_from_date       => v_valid_from,
                                                i_valid_to_date         => NULL,
                                                i_change_user           => v_userid,
                                                i_mapping_type          => 'JU',
                                                i_action_type           => 'INSERT');
                                               
                                    --do the mapping changes also for all the other companies (Rep Office and Virtual) which uses this company as legal company
                                    IF (v_company_type_cd = 'L')
                                        THEN
                                       
                                        FOR V_REC in (select company_cd from cfg_v_companies where legal_company_cd = :new.company_cd and valid_ind = 'Y' and cbc_gbe_scope = 'Y' and company_type_cd in ('O','V'))
                                        LOOP
                                       
                                        mdm_util_companies.modifycompanymapping_ce_ju (
                                                i_company_cd            => v_rec.company_cd,
                                                i_reporting_entity_cd   => 'J-' || v_country_cd,
                                                i_valid_from_date       => v_valid_from,
                                                i_valid_to_date         => NULL,
                                                i_change_user           => v_userid,
                                                i_mapping_type          => 'JU',
                                                i_action_type           => 'INSERT');
                                               
                                        END LOOP;
                                    END IF;


                                 END IF;
                               
                            ELSE
                            --update the existing address P/L with valid_from
                            MDM_UTIL_ADDRESSES.modify_company_address(p_company_cd => :new.company_cd
                                                                       ,p_address_type_cd  => :new.address_type_cd
                                                                       ,p_additional_name => :new.additional_name
                                                                       ,p_street => :new.street
                                                                       ,p_house_no => :new.house_no
                                                                       ,p_building  => :new.building
                                                                       ,p_additional_info => :new.additional_info
                                                                       ,p_zip_code => :new.zip_code
                                                                       ,p_city=> :new.city
                                                                       ,p_district_name => :new.district_name
                                                                       ,p_country_id => :new.country_id
                                                                       ,p_latitude => :new.latitude
                                                                       ,p_longitude => :new.longitude
                                                                       ,p_address_remark => :new.address_remark
                                                                       ,p_valid_from => :new.valid_from
                                                                       ,p_action_type => 'UPDATE');


                        END IF;
        END IF;


    END IF;
       


    IF (nvl(:new.address_type_cd, :old.address_type_cd) not in ( 'P','L'))
        THEN
            IF (cntr = 0)
                THEN
                    --insert address different than P, L address type with valid_from date
                    MDM_UTIL_ADDRESSES.modify_company_address(p_company_cd => :new.company_cd
                                                               ,p_address_type_cd  => :new.address_type_cd
                                                               ,p_additional_name => :new.additional_name
                                                               ,p_street => :new.street
                                                               ,p_house_no => :new.house_no
                                                               ,p_building  => :new.building
                                                               ,p_additional_info => :new.additional_info
                                                               ,p_zip_code => :new.zip_code
                                                               ,p_city=> :new.city
                                                               ,p_district_name => :new.district_name
                                                               ,p_country_id => :new.country_id
                                                               ,p_latitude => :new.latitude
                                                               ,p_longitude => :new.longitude
                                                               ,p_address_remark => :new.address_remark
                                                               ,p_valid_from => :new.valid_from
                                                               ,p_action_type => 'INSERT');
                                                   
                ELSE
                    --update address different than P, L address type with valid_from date
                    MDM_UTIL_ADDRESSES.modify_company_address(p_company_cd => :new.company_cd
                                                                           ,p_address_type_cd  => :new.address_type_cd
                                                                           ,p_additional_name => :new.additional_name
                                                                           ,p_street => :new.street
                                                                           ,p_house_no => :new.house_no
                                                                           ,p_building  => :new.building
                                                                           ,p_additional_info => :new.additional_info
                                                                           ,p_zip_code => :new.zip_code
                                                                           ,p_city=> :new.city
                                                                           ,p_district_name => :new.district_name
                                                                           ,p_country_id => :new.country_id
                                                                           ,p_latitude => :new.latitude
                                                                           ,p_longitude => :new.longitude
                                                                           ,p_address_remark => :new.address_remark
                                                                           ,p_valid_from => :new.valid_from
                                                                           ,p_action_type => 'UPDATE');
                                                                           
            END IF;
   
    END IF;


END IF;


IF (DELETING)
    THEN
   
    IF (nvl(:new.address_type_cd, :old.address_type_cd) in ('L','P'))
        THEN
            RAISE err_not_allowed_to_invalidate;
   
    END IF;


    MDM_UTIL_ADDRESSES.modify_company_address(p_company_cd => nvl(:new.company_cd, :old.company_cd)
                                           ,p_address_type_cd  => nvl(:new.address_type_cd, :old.address_type_cd)
                                           ,p_action_type => 'DELETE');


         
END IF;
EXCEPTION
    WHEN err_upd
    THEN
        raise_application_error (-20111, 'The address cannot be updated because the Address type is different. Old address type: '||:old.address_type_cd||' New address type: '||:new.address_type_cd);
    WHEN err_ins
    THEN
        raise_application_error (-20112, 'An address already exists for this Company and Address type. To modify the existing address, please use the Update button.');
    WHEN err_ctry_chg
    THEN
        raise_application_error (-20113, 'The company country modified but not the Valid From Date. Please update also the Valid From Date.');  
        WHEN test_err
    THEN
        raise_application_error (-20113, 'New: '||:new.company_cd||' Old:'||:old.company_cd||'Count: '||cntr);
    WHEN err_ins_legal_addr
    THEN
        raise_application_error (-20113, 'The legal address cannot be inserted for this type of company');
    WHEN err_not_allowed_to_invalidate
    THEN
        raise_application_error (-20113, 'It is not allowed to invalidate/delete this type of address');
       
       
END;