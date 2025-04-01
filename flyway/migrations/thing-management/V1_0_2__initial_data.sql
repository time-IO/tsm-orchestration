
insert into "user" (id, name, password, first_name, last_name, email)
values  (1, 'Test', 'hiddenpw', 'Test', 'User', 'test@gmail.de');

insert into database (id, schema, "user", password, ro_user, ro_password)
values  (1, 'meinprojekt_2c8fe389986948b0a54d4f949756790c', 'meinprojekt_9e6af763c8a44885afd706712795528c', 'QMNskmigCidaG7bi6i3CKoum', 'ro_meinprojekt_6f5d4b849e5c45a0832d9c73be978b41', 'xB89qumZOU2f8DBlyMWDzWZN');

insert into mqtt (id, "user", password)
values (1, 'meinprojekt_36627cc49ef440178495a23c24dde39e', 'W9mkdi8JKQZX6gbtJbHlUI0V57QbK0OkZwHPVulu');

insert into project (id, name, uuid, database_id, mqtt_id)
values  (1, 'Mein Projekt', 'fc825a0a-306b-4e85-881d-dc4f06873a2b', 1, 1);

insert into lnk_project_user (id, project_id, user_id)
values  (1, 1, 1);
