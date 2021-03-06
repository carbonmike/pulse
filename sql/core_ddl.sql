CREATE TABLE "active_sessions" (
  "id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "session_type_ref_id" int2 NOT NULL,
  "session_profile_ref_id" int2,
  "created_ts" timestamptz(255) NOT NULL,
  "expired_ts" timestamptz(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "group_memberships" (
  "user_id" uuid NOT NULL,
  "group_id" uuid NOT NULL,
  PRIMARY KEY ("user_id", "group_id")
);

CREATE TABLE "groups" (
  "id" uuid NOT NULL,
  "name" varchar(255) NOT NULL,
  "description" text,
  "is_active" bool NOT NULL,
  "created_ts" timestamptz NOT NULL,
  "deleted_ts" timestamptz,
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_action_types" (
  "id" int2 NOT NULL,
  "name" varchar(64) NOT NULL,
  "description" varchar(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_asset_types" (
  "id" int2 NOT NULL,
  "name" varchar(64) NOT NULL,
  "description" varchar(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_entity_types" (
  "id" int2 NOT NULL,
  "name" varchar(64) NOT NULL,
  "entity_table_name" varchar(32) NOT NULL,
  "entity_table_pk_column" varchar(32) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_session_init_types" (
  "id" int2 NOT NULL,
  "name" varchar(16) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_session_profiles" (
  "id" int2 NOT NULL,
  "name" varchar(64),
  "session_ttl_seconds" int2 NOT NULL,
  "init_type_ref_id" int2 NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_session_types" (
  "id" int2 NOT NULL,
  "name" varchar(16) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "ref_storage_profiles" (
  "id" int2 NOT NULL,
  "name" varchar(32) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "role_assignments" (
  "id" uuid NOT NULL,
  "entity_type_ref_id" int2 NOT NULL,
  "entity_id" uuid NOT NULL,
  "role_id" uuid NOT NULL,
  "created_ts" timestamptz(255) NOT NULL,
  "deleted_ts" timestamptz(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "roles" (
  "id" uuid NOT NULL,
  "action_type_ref_id" int2 NOT NULL,
  "asset_type_ref_id" int2 NOT NULL,
  "name" varchar(64) NOT NULL,
  "tag" varchar(255) NOT NULL,
  "description" varchar(255),
  "created_ts" timestamptz NOT NULL,
  "is_active" bool NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "users" (
  "id" uuid NOT NULL,
  "username" varchar(64) NOT NULL,
  "password" varchar(255) NOT NULL,
  "email" varchar(255) NOT NULL,
  "public_key_uri" text,
  "default_session_type_ref_id" int2,
  "storage_profile_ref_id" int2,
  "status" int2 NOT NULL,
  "created_ts" timestamptz(255) NOT NULL,
  "deleted_ts" timestamptz(255),
  PRIMARY KEY ("id")
);

ALTER TABLE "active_sessions" ADD CONSTRAINT "fk_active_sessions_users_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");
ALTER TABLE "active_sessions" ADD CONSTRAINT "fk_active_sessions_ref_session_types_1" FOREIGN KEY ("session_type_ref_id") REFERENCES "ref_session_types" ("id");
ALTER TABLE "active_sessions" ADD CONSTRAINT "fk_active_sessions_ref_session_profiles_1" FOREIGN KEY ("session_profile_ref_id") REFERENCES "ref_session_profiles" ("id");
ALTER TABLE "group_memberships" ADD CONSTRAINT "fk_group_memberships_users_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");
ALTER TABLE "group_memberships" ADD CONSTRAINT "fk_group_memberships_groups_1" FOREIGN KEY ("group_id") REFERENCES "groups" ("id");
ALTER TABLE "role_assignments" ADD CONSTRAINT "fk_role_assignments_ref_entity_types_1" FOREIGN KEY ("entity_type_ref_id") REFERENCES "ref_entity_types" ("id");
ALTER TABLE "roles" ADD CONSTRAINT "fk_roles_ref_asset_types_1" FOREIGN KEY ("asset_type_ref_id") REFERENCES "ref_asset_types" ("id");
ALTER TABLE "roles" ADD CONSTRAINT "fk_roles_ref_action_types_1" FOREIGN KEY ("action_type_ref_id") REFERENCES "ref_action_types" ("id");

