select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select country
from `pipeline-466508`.`ecommerce_analytics`.`users_by_country`
where country is null



      
    ) dbt_internal_test