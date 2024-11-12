BEGIN;

-- public.contact definition

CREATE TABLE public.measured_quantity (
	id              serial4 NOT NULL PRIMARY KEY,
	term            varchar(255) NOT NULL,
    provenance_uri  varchar(255),
    definition      text
);

CREATE TABLE public.license (
	id                  int4 not null,
    term                varchar(255) not null,
    provenance_uri      varchar(255),
    provenance          text,
    definition          text
);

CREATE TABLE public.aggregation_type (
	id                  int4 not null,
    term                varchar(255) not null,
    definition          text
);

CREATE TABLE public.unit (
	id                  int4 not null,
    term                varchar(255) not null,
    definition          text,
    provenance          text
);

COMMIT;