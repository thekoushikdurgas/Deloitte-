CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."CER_V_RSG_IOF" INSTEAD OF
    DELETE ON MDMAPPL.CER_V_RATE_SUBSCRIPT_GRPS_MTN REFERENCING NEW AS NEW OLD AS OLD
DECLARE
BEGIN
    IF DELETING THEN
        BEGIN
 /*
       first delete child records in cer_rate_subscriptions
     */
            DELETE CER.CER_V_RATE_SUBSCRIPTIONS
            WHERE
                MEMBER_OF_RSG_CD = :OLD.RSG_CD;
 /*
       then delete record in cer_rate_subscription_groups
     */
            DELETE CER.CER_V_RATE_SUBSCRIPTION_GROUPS
            WHERE
                RSG_CD = :OLD.RSG_CD;
        END;
    END IF;
END;
/

ALTER TRIGGER "MDMAPPL"."CER_V_RSG_IOF" ENABLE;