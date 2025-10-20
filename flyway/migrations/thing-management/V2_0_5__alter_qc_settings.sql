alter table qaqc_setting_function
    add field jsonb;

alter table qaqc_setting_function
    add target jsonb;

alter table qaqc_setting
    drop column thing_id;