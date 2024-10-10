BEGIN;

-- public.contact definition

CREATE TABLE public.measured_quantity (
	id              serial4 NOT NULL PRIMARY KEY,
	term            varchar(255) NOT NULL,
    provenance_uri  varchar(255),
    definition      text
);

COMMIT;