CREATE OR REPLACE EDITIONABLE TRIGGER "MDMAPPL"."CER_V_EXCHANGE_RATES_IOF" INSTEAD OF
    INSERT OR DELETE OR UPDATE ON MDMAPPL.CER_V_EXCHANGE_RATES_MTN REFERENCING NEW AS NEW OLD AS OLD
DECLARE
    E_UPD EXCEPTION;
 /*
=======================================================================
                 (c) 2005 - F. Hoffmann La Roche AG
-----------------------------------------------------------------------
   trigger     : CER_V_EXCHANGE_RATES_IOF
   This is part of the CER application.
-----------------------------------------------------------------------
   Purpose


   Prevent records of table CER_V_EXCHANGE_RATES from being updated if
   one of the following columns has been altered
        o xrt_cd
        o currency_cd
        o rate_period
        o plan_period


-----------------------------------------------------------------------
   Persons involved
   Short Name  Name                      Contact
   AME         Andreas Mengel, Trivadis  andreas.mengel@trivadis.com
-----------------------------------------------------------------------
   Change History


   30.11.05   AME    created
   21.10.2016 OlA   Add gov rate


=======================================================================
*/
BEGIN
    IF INSERTING THEN
        IF :NEW.XRT_CD NOT LIKE 'G0%' THEN
            INSERT INTO CER_EXCHANGE_RATES (
                XRT_CD,
                CURRENCY_CD,
                RATE_PERIOD,
                PLAN_PERIOD,
                RATE,
                SCALING_FACTOR,
                VALID_IND
            ) VALUES (
                :NEW.XRT_CD,
                :NEW.CURRENCY_CD,
                :NEW.RATE_PERIOD,
                NVL(:NEW.PLAN_PERIOD, '-'),
                :NEW.RATE,
                :NEW.SCALING_FACTOR,
                :NEW.VALID_IND
            );
        ELSE
            INSERT INTO CER_V_CENTRAL_GOV_RATES (
                XRT_CD,
                CURRENCY_CD_1,
                CURRENCY_CD_2,
                RATE_PERIOD,
                RATE,
                SCALING_FACTOR,
                VALID_IND
            ) VALUES (
                :NEW.XRT_CD,
                :NEW.CURRENCY_CD,
                :NEW.CURRENCY_CD_2,
                :NEW.RATE_PERIOD,
                :NEW.RATE,
                :NEW.SCALING_FACTOR,
                :NEW.VALID_IND
            );
        END IF;
    ELSIF (UPDATING) THEN
        IF :NEW.XRT_CD != :OLD.XRT_CD OR :NEW.CURRENCY_CD != :OLD.CURRENCY_CD OR :NEW.RATE_PERIOD != :OLD.RATE_PERIOD OR NVL(:NEW.PLAN_PERIOD, '-') != NVL(:OLD.PLAN_PERIOD, '-') THEN
            RAISE E_UPD;
        END IF;

        IF :NEW.XRT_CD NOT LIKE 'G0%' THEN
            UPDATE CER_EXCHANGE_RATES
            SET
                RATE = :NEW.RATE,
                SCALING_FACTOR = :NEW.SCALING_FACTOR,
                VALID_IND = :NEW.VALID_IND
            WHERE
                XRT_CD = :NEW.XRT_CD
                AND CURRENCY_CD = :NEW.CURRENCY_CD
                AND RATE_PERIOD = :NEW.RATE_PERIOD
                AND PLAN_PERIOD = :NEW.PLAN_PERIOD;
        ELSE
            UPDATE CER_V_CENTRAL_GOV_RATES
            SET
                RATE = :NEW.RATE,
                SCALING_FACTOR = :NEW.SCALING_FACTOR,
                VALID_IND = :NEW.VALID_IND
            WHERE
                XRT_CD = :NEW.XRT_CD
                AND CURRENCY_CD_1 = :NEW.CURRENCY_CD
                AND CURRENCY_CD_2 = :NEW.CURRENCY_CD_2
                AND RATE_PERIOD = :NEW.RATE_PERIOD;
        END IF;
    ELSIF (DELETING) THEN
        IF :NEW.XRT_CD NOT LIKE 'G0%' THEN
            DELETE CER_EXCHANGE_RATES
            WHERE
                XRT_CD = :OLD.XRT_CD
                AND CURRENCY_CD = :OLD.CURRENCY_CD
                AND RATE_PERIOD = :OLD.RATE_PERIOD
                AND PLAN_PERIOD = :OLD.PLAN_PERIOD;
        ELSE
            DELETE FROM CER_V_CENTRAL_GOV_RATES
            WHERE
                XRT_CD = :OLD.XRT_CD
                AND RATE = :OLD.RATE
                AND CURRENCY_CD_1 = :OLD.CURRENCY_CD
                AND CURRENCY_CD_2 = :OLD.CURRENCY_CD_2
                AND RATE_PERIOD = :OLD.RATE_PERIOD;
        END IF;
    END IF;
EXCEPTION
    WHEN E_UPD THEN
        RAISE_APPLICATION_ERROR (-20101, 'CER_V_EXCHANGE_RATES_IOF');
END;
/

ALTER TRIGGER "MDMAPPL"."CER_V_EXCHANGE_RATES_IOF" ENABLE;