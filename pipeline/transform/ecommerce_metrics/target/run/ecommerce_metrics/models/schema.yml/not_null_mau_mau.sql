select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select mau
from `pipeline-466508`.`ecommerce_analytics`.`mau`
where mau is null



      
    ) dbt_internal_test