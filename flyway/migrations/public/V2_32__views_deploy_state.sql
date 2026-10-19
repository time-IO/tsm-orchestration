CREATE TABLE IF NOT EXISTS public.views_deploy_state (
    schema      text NOT NULL,
    kind        text NOT NULL,
    version     text NOT NULL,
    deployed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (schema, kind)
);
