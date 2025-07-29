DROP TABLE IF EXISTS "FEATURES" CASCADE;
CREATE TABLE "FEATURES"
(
    "ID"            serial,
    "NAME"          text,
    "DESCRIPTION"   text,
    "ENCODING_TYPE" text,
    "FEATURE"       jsonb,
    "PROPERTIES"    jsonb
)
