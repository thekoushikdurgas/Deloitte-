CREATE OR REPLACE TRIGGER complex_nested_trigger
    AFTER INSERT ON sales_orders
    FOR EACH ROW
BEGIN
    DECLARE
        v_outer_counter NUMBER := 1;
        v_inner_counter NUMBER;
    BEGIN
        -- Nested basic loops with labels
        <<outer_loop>>
        LOOP
            v_inner_counter := 1;
            
            <<inner_loop>>
            LOOP
                INSERT INTO sales_analytics 
                VALUES (:NEW.order_id, v_outer_counter, v_inner_counter, SYSDATE);
                
                v_inner_counter := v_inner_counter + 1;
                EXIT inner_loop WHEN v_inner_counter > 3;
            END LOOP inner_loop;
            
            v_outer_counter := v_outer_counter + 1;
            EXIT outer_loop WHEN v_outer_counter > 5;
        END LOOP outer_loop;
    END;
END;
/
