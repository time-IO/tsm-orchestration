ALTER TABLE observation ADD COLUMN id BIGINT;
CREATE SEQUENCE observation_id_seq;
UPDATE observation SET id = nextval('observation_test_id_seq');
ALTER TABLE observation ADD CONSTRAINT pk_observation PRIMARY KEY (id);
