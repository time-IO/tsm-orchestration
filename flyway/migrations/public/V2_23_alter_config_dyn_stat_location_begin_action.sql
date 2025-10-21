

-- MV neu erstellen mit valid_range
CREATE MATERIALIZED VIEW sms_configuration_static_location_begin_action_neu AS
SELECT *,
       tstzrange(begin_date, COALESCE(end_date,'infinity'::timestamptz)) AS valid_range
FROM public.configuration_static_location_begin_action;


CREATE INDEX idx_sla_configuration_id
ON sms_configuration_static_location_begin_action_neu (configuration_id);

CREATE INDEX idx_sla_valid_range
ON sms_configuration_static_location_begin_action_neu USING gist (valid_range);


CREATE MATERIALIZED VIEW sms_configuration_dynamic_location_begin_action_neu AS
SELECT *,
       tstzrange(begin_date, COALESCE(end_date,'infinity'::timestamptz)) AS valid_range
FROM public.configuration_dynamic_location_begin_action;


CREATE INDEX idx_sla_configuration_id
ON sms_configuration_dynamic_location_begin_action_neu (configuration_id);

CREATE INDEX idx_sla_valid_range
ON sms_configuration_dynamic_location_begin_action_neu USING gist (valid_range);