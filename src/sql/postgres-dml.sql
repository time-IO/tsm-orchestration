INSERT INTO relation_role
    (id, name, definition, inverse_name, inverse_definition, description, properties)
VALUES
    (1, 'created_by', 'This was created by other(s)', 'created', 'Other(s) created this', 'A derived product', null)
ON CONFLICT (id) DO UPDATE SET
    name = excluded.name,
    definition = excluded.definition,
    inverse_name = excluded.inverse_name,
    inverse_definition = excluded.inverse_definition,
    description = excluded.description,
    properties = excluded.properties;
