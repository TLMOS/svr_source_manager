CREATE TABLE "user"
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "password" VARCHAR(256) NOT NULL,
  max_sources INT NOT NULL DEFAULT 5,
  "role" INT NOT NULL DEFAULT 0,
  UNIQUE ("name")
);

CREATE TABLE source
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "url" TEXT NOT NULL,
  status_code INT NOT NULL,
  status_msg TEXT,
  user_id INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES "user"(id)
);

CREATE TABLE video_chunk
(
  id SERIAL PRIMARY KEY,
  file_path TEXT NOT NULL,
  start_time FLOAT NOT NULL,
  end_time FLOAT NOT NULL,
  source_id INT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES source(id),
  UNIQUE (file_path)
);

CREATE INDEX CONCURRENTLY "index_user_id"
ON "user" using btree (id);

CREATE INDEX CONCURRENTLY "index_user_name"
ON "user" using btree (name);

CREATE INDEX CONCURRENTLY "index_source_id_and_user_id"
ON source using btree (id, user_id);

CREATE INDEX CONCURRENTLY "index_video_chunk_id"
ON video_chunk using btree (id);

