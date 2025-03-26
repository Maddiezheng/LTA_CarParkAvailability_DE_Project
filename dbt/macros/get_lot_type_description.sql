{#
    This macro returns the description of the lot_type
#}
{% macro get_lot_type_description(lot_type) -%}
    case {{ dbt.safe_cast("lot_type", api.Column.translate_type("string")) }}  
        when 'C' then 'Car'
        when 'H' then 'Heavy Vehicle'
        when 'M' then 'Motorcycle'
        when 'Y' then 'Motorcycle'
        else 'Unknown'
    end
{%- endmacro %}