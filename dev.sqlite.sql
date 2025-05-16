BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num"	VARCHAR(32) NOT NULL,
	CONSTRAINT "alembic_version_pkc" PRIMARY KEY("version_num")
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"email"	VARCHAR(64) NOT NULL,
	"username"	VARCHAR(64) NOT NULL,
	"password_hash"	VARCHAR(128) NOT NULL,
	"first_name"	VARCHAR(64) NOT NULL,
	"last_name"	VARCHAR(64) NOT NULL,
	"phone_number"	VARCHAR(20) NOT NULL,
	"is_approved"	BOOLEAN,
	"created_at"	DATETIME,
	"last_login"	DATETIME,
	"user_type"	VARCHAR(20) NOT NULL,
	"region"	VARCHAR(20) NOT NULL DEFAULT 'nairobi',
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "crop_health" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"assessment_date"	DATETIME,
	"status"	VARCHAR(50) NOT NULL,
	"notes"	TEXT,
	"image_url"	VARCHAR(200),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "sensors" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"sensor_type"	VARCHAR(50) NOT NULL,
	"location"	VARCHAR(200) NOT NULL,
	"install_date"	DATETIME,
	"last_maintenance"	DATETIME,
	"status"	VARCHAR(20),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "weather_data" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"timestamp"	DATETIME,
	"temperature"	FLOAT NOT NULL,
	"humidity"	FLOAT NOT NULL,
	"rainfall"	FLOAT,
	"wind_speed"	FLOAT,
	"condition"	VARCHAR(50) NOT NULL,
	FOREIGN KEY("farm_id") REFERENCES "farms"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "alerts" (
	"id"	INTEGER NOT NULL,
	"alert_type"	VARCHAR(50) NOT NULL,
	"message"	TEXT NOT NULL,
	"severity"	VARCHAR(20),
	"is_read"	BOOLEAN,
	"farm_id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"created_at"	DATETIME,
	"status"	VARCHAR(20),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id"),
	FOREIGN KEY("user_id") REFERENCES "users"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "farm_images" (
	"id"	INTEGER NOT NULL,
	"filename"	VARCHAR(255),
	"path"	VARCHAR(255),
	"image_type"	VARCHAR(50),
	"processed"	BOOLEAN,
	"processing_results"	TEXT,
	"farm_id"	INTEGER NOT NULL,
	"user_id"	INTEGER,
	"upload_date"	DATETIME,
	"image_url"	VARCHAR(200) NOT NULL,
	FOREIGN KEY("user_id") REFERENCES "users"("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "farms" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(100) NOT NULL,
	"location"	VARCHAR(200) NOT NULL,
	"size_acres"	FLOAT,
	"crop_type"	VARCHAR(50) NOT NULL,
	"description"	TEXT,
	"user_id"	INTEGER NOT NULL,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	"size"	FLOAT NOT NULL,
	"latitude"	FLOAT,
	"longitude"	FLOAT,
	"region"	VARCHAR(100),
	"soil_type"	VARCHAR(50),
	"ph_level"	FLOAT,
	"soil_notes"	TEXT,
	"irrigation_type"	VARCHAR(50),
	"water_source"	VARCHAR(50),
	PRIMARY KEY("id"),
	FOREIGN KEY("user_id") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "sensor_data" (
	"id"	INTEGER NOT NULL,
	"sensor_type"	VARCHAR(50),
	"value"	FLOAT NOT NULL,
	"unit"	VARCHAR(20),
	"latitude"	FLOAT,
	"longitude"	FLOAT,
	"timestamp"	DATETIME,
	"farm_id"	INTEGER,
	"user_id"	INTEGER,
	"sensor_id"	INTEGER NOT NULL,
	"status"	VARCHAR(20),
	PRIMARY KEY("id"),
	FOREIGN KEY("user_id") REFERENCES "users"("id"),
	CONSTRAINT "fk_sensor_data_sensor_id_sensors" FOREIGN KEY("sensor_id") REFERENCES "sensors"("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id")
);
CREATE TABLE IF NOT EXISTS "farm_stages" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"stage_name"	VARCHAR(50) NOT NULL,
	"start_date"	DATETIME,
	"end_date"	DATETIME,
	"status"	VARCHAR(20),
	"description"	TEXT,
	PRIMARY KEY("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id")
);
CREATE TABLE IF NOT EXISTS "pest_control" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"pest_name"	VARCHAR(100) NOT NULL,
	"detection_date"	DATETIME,
	"severity"	VARCHAR(20),
	"location_in_farm"	VARCHAR(100),
	"description"	TEXT,
	"status"	VARCHAR(20),
	"image_url"	VARCHAR(200),
	"detected_by"	VARCHAR(50),
	PRIMARY KEY("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id")
);
CREATE TABLE IF NOT EXISTS "labor_tasks" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"stage_id"	INTEGER,
	"task_name"	VARCHAR(100) NOT NULL,
	"description"	TEXT,
	"assigned_to"	VARCHAR(100),
	"start_date"	DATETIME,
	"end_date"	DATETIME,
	"status"	VARCHAR(20),
	"priority"	VARCHAR(20),
	"labor_hours"	FLOAT,
	"cost"	FLOAT,
	PRIMARY KEY("id"),
	FOREIGN KEY("stage_id") REFERENCES "farm_stages"("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id")
);
CREATE TABLE IF NOT EXISTS "pest_actions" (
	"id"	INTEGER NOT NULL,
	"pest_control_id"	INTEGER NOT NULL,
	"action_type"	VARCHAR(50) NOT NULL,
	"action_name"	VARCHAR(100) NOT NULL,
	"description"	TEXT,
	"application_date"	DATETIME,
	"scheduled_date"	DATETIME,
	"status"	VARCHAR(20),
	"effectiveness"	VARCHAR(20),
	"cost"	FLOAT,
	"user_id"	INTEGER,
	PRIMARY KEY("id"),
	FOREIGN KEY("pest_control_id") REFERENCES "pest_control"("id"),
	FOREIGN KEY("user_id") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "farm_team_members" (
	"id"	INTEGER NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"role"	VARCHAR(20) NOT NULL,
	"added_at"	DATETIME,
	"added_by"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id"),
	FOREIGN KEY("user_id") REFERENCES "users"("id"),
	FOREIGN KEY("added_by") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "fields" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(64) NOT NULL,
	"farm_id"	INTEGER NOT NULL,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	PRIMARY KEY("id"),
	FOREIGN KEY("farm_id") REFERENCES "farms"("id")
);
CREATE TABLE IF NOT EXISTS "boundary_markers" (
	"id"	INTEGER NOT NULL,
	"field_id"	INTEGER NOT NULL,
	"latitude"	FLOAT NOT NULL,
	"longitude"	FLOAT NOT NULL,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	PRIMARY KEY("id"),
	FOREIGN KEY("field_id") REFERENCES "fields"("id")
);
INSERT INTO "alembic_version" VALUES ('f59e8e6840e4');
INSERT INTO "users" VALUES (1,'ogodfrey135@gmail.com','otieno@gmail.com','scrypt:32768:8:1$UdNdYLCtjcL1F1RJ$b9fcdddc5a30ad8b293df900b0591408cb6aa93198e7855c8d91bd0deddb97f7c756fd1b2dcac7030ba804f88315810fb38bb1f5f38cd4dcac81df4ca70b9524','Godfrey','Otieno','0741768058',0,'2025-05-08 08:04:59.724683',NULL,'large-scale','nairobi');
INSERT INTO "users" VALUES (2,'makau@gmail.com','mutuse','scrypt:32768:8:1$SSRCtwYuitqsOQXg$cc353d771838e30af36502289c56ea66c102b5bd56f38eb810893faa29a81de11db099301e521fab7c4f1393598625a53cd1d6b26bd2502eae98f5806a9fb918','makau','mutua','0700123456',0,'2025-05-08 08:07:50.649213',NULL,'cooperative','nairobi');
INSERT INTO "users" VALUES (3,'kaka@gmail.com','kaka@gmail.com','scrypt:32768:8:1$R7YtehWKyF9SaLUq$10d71198218d445e8a8ab60b399a9c05a9170344b8ff6d039b2077734c9d850599f42869a1683e5eb1a881a611ec8f8bff133c72fd152558e6ad19ddd70d7874','kaka','sacco','0725220788',0,'2025-05-08 08:19:21.612937',NULL,'cooperative','nairobi');
INSERT INTO "users" VALUES (4,'simiyumaxwell@gmail.com','Simiyu','scrypt:32768:8:1$cBx3XeW2BoUxvBF4$1b7c8900d3c86b27d9f1b641a352df337c3052ff1cdd9ac5ebd531f6478f67299a8e5f740c6ca6dc4b84d300c4f597d10deeb871077d5638699a2686fb0e1c5b','Maxwell','Simiyu','+254741125435',0,'2025-05-09 20:54:03.212940',NULL,'small-scale','nairobi');
INSERT INTO "users" VALUES (5,'simiyumaxwell490@gmail.com','SimiyuMax','scrypt:32768:8:1$m7vA5qBaToItmGGD$c08a04c8fc80cac0447b3973880fa629093143da4e6b05e812807d67073f2205bcedc3686a23632dbd93562c2779be2c84b580b2c040c380f01533f00525834d','Maxwell','Simiyu','+254741125435',1,'2025-05-10 05:41:54.141869','2025-05-10 06:53:57.517854','small-scale','nairobi');
INSERT INTO "users" VALUES (6,'simiyumaxwell8090@gmail.com','SimiyuMax45','scrypt:32768:8:1$fOW6jzTzcfHgX8Z0$e5a0d4e4f4e0c5fb4ac80737fb9371d78774b7d6bb17c5e304d0f99d2a10b82f5e68fd3747fb602e960d474562e5ce604e756d6d34c30f26d6ce833fc96c8307','Maxwell','Simiyu','+254741125435',1,'2025-05-13 08:30:14.204591','2025-05-13 08:31:59.352510','small-scale','nairobi');
CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_username" ON "users" (
	"username"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_email" ON "users" (
	"email"
);
COMMIT;
